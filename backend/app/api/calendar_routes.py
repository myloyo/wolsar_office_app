from datetime import date, datetime, time, timedelta

from fastapi import APIRouter
from sqlalchemy import select

from app.api.routes import CurrentActor, Session
from app.api.schemas.calendar import EventInput, RoomInput, SlotInput
from app.application.calendar import CalendarService
from app.application.types import Record
from app.constants.calendar import SARATOV_TIMEZONE
from app.domain.access import require_admin
from app.infrastructure.calendar import SqlCalendarStore
from app.infrastructure.models.calendar import RoomRow

router = APIRouter(prefix="/api", tags=["Календарь"])


@router.get("/events")
async def events(start: date, end: date, session: Session, actor: CurrentActor) -> list[Record]:
    if end < start or (end - start).days > 366:
        raise ValueError("Выберите период не более года")
    zone = SARATOV_TIMEZONE
    return await CalendarService(SqlCalendarStore(session)).events(
        actor,
        datetime.combine(start, time(), zone),
        datetime.combine(end + timedelta(days=1), time(), zone),
    )


@router.post("/events", status_code=201)
async def add_event(data: EventInput, session: Session, actor: CurrentActor) -> Record:
    return await CalendarService(SqlCalendarStore(session)).save(actor, None, data.model_dump())


@router.put("/events/{event_id}")
async def save_event(
    event_id: int, data: EventInput, session: Session, actor: CurrentActor
) -> Record:
    return await CalendarService(SqlCalendarStore(session)).save(actor, event_id, data.model_dump())


@router.get("/rooms")
async def rooms(session: Session, actor: CurrentActor) -> list[Record]:
    return [
        {"id": r.id, "name": r.name}
        for r in await session.scalars(select(RoomRow).order_by(RoomRow.id))
    ]


@router.post("/rooms", status_code=201)
async def add_room(data: RoomInput, session: Session, actor: CurrentActor) -> Record:
    require_admin(actor)
    row = RoomRow(name=data.name, revision=1)
    session.add(row)
    await session.commit()
    return {"id": row.id, "name": row.name}


@router.get("/slots")
async def slots(session: Session, actor: CurrentActor) -> list[Record]:
    return await CalendarService(SqlCalendarStore(session)).slots(actor)


@router.post("/slots", status_code=201)
async def add_slot(data: SlotInput, session: Session, actor: CurrentActor) -> Record:
    return await CalendarService(SqlCalendarStore(session)).add_slot(actor, data.model_dump())


@router.post("/slots/{slot_id}/signup")
async def signup(slot_id: int, session: Session, actor: CurrentActor) -> Record:
    return await CalendarService(SqlCalendarStore(session)).signup(actor, slot_id, False)


@router.post("/slots/{slot_id}/replacement")
async def replacement(slot_id: int, session: Session, actor: CurrentActor) -> Record:
    return await CalendarService(SqlCalendarStore(session)).signup(actor, slot_id, True)
