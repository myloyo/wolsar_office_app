import copy
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.types import Record
from app.constants.calendar import SARATOV_TIMEZONE
from app.domain.exceptions import ConflictError
from app.infrastructure.mappers.calendar import event_record
from app.infrastructure.models.calendar import CeremonyRow, EventRow, PrayerRow
from app.infrastructure.models.workspace import UserRow


def initial_program() -> Record:
    return {
        "blocks": [
            {"id": str(i), "name": name, "minutes": minutes, "owner_id": None, "note": ""}
            for i, (name, minutes) in enumerate(
                [("Приветствие", 3), ("Прославление", 15), ("Проповедь", 40), ("Закрытие", 5)]
            )
        ],
        "assignments": {},
        "mc": {
            "host_id": None,
            "value": "Служение",
            "text": "",
            "story": "",
            "slides": "",
            "ready": False,
        },
    }


def timer_state(timer: Record) -> Record:
    result = dict(timer)
    if result.get("running") and result.get("started_at"):
        elapsed = max(
            0, (datetime.now(UTC) - datetime.fromisoformat(result["started_at"])).total_seconds()
        )
        result["remaining"] = max(0, result["remaining"] - int(elapsed))
        if result["remaining"] == 0:
            result["running"] = False
    return result


class SqlWorshipStore:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_services(self, year: int) -> list[Record]:
        rows = await self.session.execute(
            select(EventRow, CeremonyRow)
            .join(CeremonyRow, CeremonyRow.event_id == EventRow.id)
            .where(
                EventRow.starts_at >= datetime(year, 1, 1, tzinfo=SARATOV_TIMEZONE).astimezone(UTC),
                EventRow.starts_at
                < datetime(year + 1, 1, 1, tzinfo=SARATOV_TIMEZONE).astimezone(UTC),
            )
            .order_by(EventRow.starts_at)
        )
        return [
            {
                **event_record(event),
                "assignments": ceremony.program.get("assignments", {}),
                "mc": ceremony.program.get("mc", {}),
            }
            for event, ceremony in rows
        ]

    async def get(self, event_id: int) -> Record:
        row = await self.session.get(CeremonyRow, event_id, populate_existing=True)
        event = await self.session.get(EventRow, event_id)
        if row is None or event is None:
            raise LookupError("Собрание не найдено")
        return {
            "event": event_record(event),
            "program": row.program,
            "timer": timer_state(row.timer),
            "version": row.version,
        }

    async def create(self, actor_id: int, data: Record) -> Record:
        day: date = data["day"]
        kind: str = data["kind"]
        key = f"{day.isoformat()}:{kind}"
        if await self.session.scalar(
            select(CeremonyRow.event_id).where(CeremonyRow.service_key == key)
        ):
            raise ConflictError("Такое собрание уже существует")
        start = datetime.combine(
            day,
            time(10 if kind == "1 ВС" else 13 if kind == "2 ВС" else 19),
            SARATOV_TIMEZONE,
        )
        event = EventRow(
            title=f"{kind} · Богослужение",
            starts_at=start.astimezone(UTC),
            ends_at=(start + timedelta(hours=2)).astimezone(UTC),
            kind="worship",
            scope="common",
            scope_id=None,
            room_id=None,
            creator_id=actor_id,
            cancelled=False,
            version=1,
        )
        self.session.add(event)
        await self.session.flush()
        self.session.add(
            CeremonyRow(
                event_id=event.id,
                service_key=key,
                program=initial_program(),
                timer={"index": 0, "remaining": 180, "running": False, "started_at": None},
                version=1,
            )
        )
        try:
            await self.session.commit()
        except IntegrityError as error:
            await self.session.rollback()
            raise ConflictError("Собрание уже создано") from error
        return await self.get(event.id)

    async def update_service_if_current(self, event_id: int, version: int, values: Record) -> None:
        changed = await self.session.scalar(
            update(CeremonyRow)
            .where(CeremonyRow.event_id == event_id, CeremonyRow.version == version)
            .values(**values, version=version + 1)
            .returning(CeremonyRow.event_id)
        )
        if changed is None:
            await self.session.rollback()
            raise ConflictError("Собрание изменилось. Обновите данные.")

    async def program(self, event_id: int, data: Record, version: int) -> Record:
        current = await self.get(event_id)
        if current["timer"]["running"]:
            raise ConflictError("Приостановите таймер перед изменением программы")
        ids = {value for value in data["assignments"].values() if value is not None}
        ids |= {b["owner_id"] for b in data["blocks"] if b["owner_id"] is not None}
        if data["mc"]["host_id"] is not None:
            ids.add(data["mc"]["host_id"])
        found = set(
            await self.session.scalars(
                select(UserRow.id).where(UserRow.id.in_(ids), UserRow.active.is_(True))
            )
        )
        if found != ids:
            raise ValueError("Один из назначенных служителей недоступен")
        await self.update_service_if_current(
            event_id,
            version,
            {
                "program": data,
                "timer": {
                    "index": 0,
                    "remaining": data["blocks"][0]["minutes"] * 60,
                    "running": False,
                    "started_at": None,
                },
            },
        )
        await self.session.commit()
        return await self.get(event_id)

    async def timer(self, event_id: int, action: str, version: int) -> Record:
        current = await self.get(event_id)
        timer = current["timer"]
        blocks = current["program"]["blocks"]
        if current["event"]["cancelled"]:
            raise ConflictError("Собрание отменено")
        if action == "start" and timer["remaining"] <= 0:
            raise ConflictError("Перейдите к следующему блоку или сбросьте таймер")
        if action == "next" and timer["index"] >= len(blocks) - 1:
            raise ConflictError("Это последний блок")
        if action == "previous" and timer["index"] == 0:
            raise ConflictError("Это первый блок")
        if action in {"next", "previous", "reset"}:
            index = (
                0
                if action == "reset"
                else max(0, min(len(blocks) - 1, timer["index"] + (1 if action == "next" else -1)))
            )
            timer = {
                "index": index,
                "remaining": blocks[index]["minutes"] * 60,
                "running": False,
                "started_at": None,
            }
        elif action == "start":
            timer.update(running=True, started_at=datetime.now(UTC).isoformat())
        elif action == "pause":
            timer.update(running=False, started_at=None)
        elif action == "minute":
            timer.update(
                remaining=timer["remaining"] + 60,
                started_at=datetime.now(UTC).isoformat() if timer["running"] else None,
            )
        await self.update_service_if_current(event_id, version, {"timer": timer})
        await self.session.commit()
        return await self.get(event_id)

    async def prayers(self, actor_id: int, all_rows: bool) -> list[Record]:
        query = select(PrayerRow).order_by(PrayerRow.id.desc())
        if not all_rows:
            query = query.where(PrayerRow.creator_id == actor_id)
        return [
            {
                "id": r.id,
                "creator_id": r.creator_id,
                "title": r.title,
                "details": r.details,
                "event_id": r.event_id,
                "status": r.status,
            }
            for r in await self.session.scalars(query)
        ]

    async def add_prayer(self, actor_id: int, data: Record) -> Record:
        row = PrayerRow(
            creator_id=actor_id, title=data["title"], details=data["details"], status="pending"
        )
        self.session.add(row)
        await self.session.commit()
        return next(r for r in await self.prayers(actor_id, False) if r["id"] == row.id)

    async def link_prayer(self, prayer_id: int, event_id: int) -> Record:
        row = await self.session.get(PrayerRow, prayer_id)
        if row is None:
            raise LookupError("Заявка не найдена")
        target = await self.get(event_id)
        if target["timer"]["running"]:
            raise ConflictError("Приостановите таймер перед изменением программы")
        block_id = f"prayer-{row.id}"
        if row.event_id and row.event_id != event_id:
            old = await self.get(row.event_id)
            if old["timer"]["running"]:
                raise ConflictError("Прежнее собрание сейчас проводится")
            program = copy.deepcopy(old["program"])
            program["blocks"] = [b for b in program["blocks"] if b["id"] != block_id]
            await self.update_service_if_current(row.event_id, old["version"], {"program": program})
        program = copy.deepcopy(target["program"])
        if not any(b["id"] == block_id for b in program["blocks"]):
            program["blocks"].insert(
                max(0, len(program["blocks"]) - 1),
                {
                    "id": block_id,
                    "name": row.title,
                    "minutes": 5,
                    "owner_id": None,
                    "note": "Особая молитва",
                },
            )
        await self.update_service_if_current(event_id, target["version"], {"program": program})
        row.event_id, row.status = event_id, "scheduled"
        await self.session.commit()
        return await self.get(event_id)
