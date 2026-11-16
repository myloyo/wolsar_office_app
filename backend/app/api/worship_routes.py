from fastapi import APIRouter

from app.api.routes import CurrentActor, Session
from app.api.schemas.worship import PrayerInput, PrayerLink, ProgramInput, ServiceInput, TimerAction
from app.application.types import Record
from app.application.worship import WorshipService
from app.infrastructure.worship import SqlWorshipStore

router = APIRouter(prefix="/api", tags=["Богослужения"])


@router.get("/services")
async def services(year: int, session: Session, actor: CurrentActor) -> list[Record]:
    if not 2020 <= year <= 2100:
        raise ValueError("Неверный год")
    return await WorshipService(SqlWorshipStore(session)).list_services(actor, year)


@router.post("/services", status_code=201)
async def create_service(data: ServiceInput, session: Session, actor: CurrentActor) -> Record:
    return await WorshipService(SqlWorshipStore(session)).create(actor, data.model_dump())


@router.get("/services/{event_id}")
async def service(event_id: int, session: Session, actor: CurrentActor) -> Record:
    return await WorshipService(SqlWorshipStore(session)).get(actor, event_id)


@router.put("/services/{event_id}/program")
async def program(
    event_id: int, data: ProgramInput, session: Session, actor: CurrentActor
) -> Record:
    return await WorshipService(SqlWorshipStore(session)).program(
        actor, event_id, data.model_dump(exclude={"expected_version"}), data.expected_version
    )


@router.post("/services/{event_id}/timer")
async def timer(event_id: int, data: TimerAction, session: Session, actor: CurrentActor) -> Record:
    return await WorshipService(SqlWorshipStore(session)).timer(
        actor, event_id, data.action, data.expected_version
    )


@router.get("/prayers")
async def prayers(session: Session, actor: CurrentActor) -> list[Record]:
    return await WorshipService(SqlWorshipStore(session)).prayers(actor)


@router.post("/prayers", status_code=201)
async def add_prayer(data: PrayerInput, session: Session, actor: CurrentActor) -> Record:
    return await WorshipService(SqlWorshipStore(session)).add_prayer(actor, data.model_dump())


@router.post("/prayers/{prayer_id}/schedule")
async def link_prayer(
    prayer_id: int, data: PrayerLink, session: Session, actor: CurrentActor
) -> Record:
    return await WorshipService(SqlWorshipStore(session)).link_prayer(
        actor, prayer_id, data.event_id
    )
