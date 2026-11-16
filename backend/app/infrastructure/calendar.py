from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.types import Record
from app.domain.exceptions import ConflictError
from app.infrastructure.mappers.calendar import event_record
from app.infrastructure.models.calendar import EventRow, RoomRow, SignupRow, SlotRow
from app.infrastructure.models.workspace import MembershipRow, MinistryRow
from app.utils.dates import aware


class SqlCalendarStore:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_events(self, start: datetime, end: datetime) -> list[Record]:
        return [
            event_record(r)
            for r in await self.session.scalars(
                select(EventRow)
                .where(
                    EventRow.starts_at < end.astimezone(UTC),
                    EventRow.ends_at > start.astimezone(UTC),
                )
                .order_by(EventRow.starts_at)
            )
        ]

    async def event(self, event_id: int) -> Record:
        row = await self.session.get(EventRow, event_id)
        if row is None:
            raise LookupError("Событие не найдено")
        return event_record(row)

    async def save(self, event_id: int | None, actor_id: int, data: Record) -> Record:
        data = dict(data)
        data["starts_at"] = data["starts_at"].astimezone(UTC)
        data["ends_at"] = data["ends_at"].astimezone(UTC)
        expected = data.pop("expected_version", None)
        if data["scope"] == "department":
            from app.infrastructure.models.workspace import DepartmentRow

            if await self.session.get(DepartmentRow, data["scope_id"]) is None:
                raise ValueError("Отделение не найдено")
        if (
            data["scope"] == "ministry"
            and await self.session.get(MinistryRow, data["scope_id"]) is None
        ):
            raise ValueError("Служение не найдено")
        if data["room_id"] is not None:
            locked = await self.session.scalar(
                update(RoomRow)
                .where(RoomRow.id == data["room_id"])
                .values(revision=RoomRow.revision + 1)
                .returning(RoomRow.id)
            )
            if locked is None:
                raise ValueError("Помещение не найдено")
            overlap = await self.session.scalar(
                select(EventRow.id)
                .where(
                    EventRow.room_id == data["room_id"],
                    EventRow.cancelled.is_(False),
                    EventRow.starts_at < data["ends_at"],
                    EventRow.ends_at > data["starts_at"],
                    EventRow.id != (event_id or 0),
                )
                .limit(1)
            )
            if overlap and not data["cancelled"]:
                await self.session.rollback()
                raise ConflictError("Помещение занято в указанное время")
        if event_id:
            changed = await self.session.scalar(
                update(EventRow)
                .where(EventRow.id == event_id, EventRow.version == expected)
                .values(**data, version=EventRow.version + 1)
                .returning(EventRow.id)
            )
            if changed is None:
                await self.session.rollback()
                raise ConflictError("Событие уже изменено. Обновите календарь.")
        else:
            row = EventRow(**data, creator_id=actor_id, version=1)
            self.session.add(row)
            await self.session.flush()
            event_id = row.id
        await self.session.commit()
        self.session.expire_all()
        return await self.event(event_id)

    async def slots(self) -> list[Record]:
        signups = list(await self.session.scalars(select(SignupRow)))
        return [
            {
                "id": s.id,
                "event_id": s.event_id,
                "ministry_id": s.ministry_id,
                "title": s.title,
                "capacity": s.capacity,
                "signups": [
                    {"user_id": r.user_id, "status": r.status} for r in signups if r.slot_id == s.id
                ],
            }
            for s in await self.session.scalars(select(SlotRow).order_by(SlotRow.id))
        ]

    async def add_slot(self, data: Record) -> Record:
        if await self.session.get(MinistryRow, data["ministry_id"]) is None:
            raise ValueError("Служение не найдено")
        row = SlotRow(**data, revision=1)
        self.session.add(row)
        await self.session.commit()
        return next(s for s in await self.slots() if s["id"] == row.id)

    async def signup(self, slot_id: int, user_id: int, cancel: bool) -> Record:
        locked = await self.session.scalar(
            update(SlotRow)
            .where(SlotRow.id == slot_id)
            .values(revision=SlotRow.revision + 1)
            .returning(SlotRow.id)
        )
        slot = await self.session.get(SlotRow, locked) if locked else None
        if slot is None:
            raise LookupError("Слот не найден")
        event = await self.session.get(EventRow, slot.event_id)
        if event is None or event.cancelled:
            raise ConflictError("Событие отменено")
        if aware(event.ends_at) <= datetime.now(UTC) and not cancel:
            raise ConflictError("Событие уже завершилось")
        row = await self.session.get(SignupRow, (slot_id, user_id))
        if cancel:
            if not row or row.status != "active":
                raise ConflictError("Активная запись не найдена")
            row.status = "replacement"
            from app.infrastructure.notifications import notify

            leaders = await self.session.scalars(
                select(MembershipRow).where(
                    MembershipRow.ministry_id == slot.ministry_id, MembershipRow.leader.is_(True)
                )
            )
            for leader in leaders:
                await notify(self.session, leader.user_id, f"Нужна замена: {slot.title}", "/slots")
        elif row and row.status == "active":
            pass
        else:
            occupied = await self.session.scalar(
                select(func.count())
                .select_from(SignupRow)
                .where(SignupRow.slot_id == slot_id, SignupRow.status == "active")
            )
            if occupied is not None and occupied >= slot.capacity:
                await self.session.rollback()
                raise ConflictError("Свободных мест больше нет")
            if row:
                row.status = "active"
            else:
                self.session.add(SignupRow(slot_id=slot_id, user_id=user_id, status="active"))
        await self.session.commit()
        return next(s for s in await self.slots() if s["id"] == slot_id)
