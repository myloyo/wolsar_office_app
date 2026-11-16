from fastapi import APIRouter
from sqlalchemy import select

from app.api.routes import CurrentActor, Session
from app.api.schemas.preparation import PreparationInput, PreparationUpdate
from app.application.types import Record
from app.constants.calendar import DEFAULT_PREPARATION_STEPS
from app.domain.access import can_read_space, can_write_space
from app.infrastructure.mappers.preparations import preparation_record
from app.infrastructure.models.calendar import PreparationRow
from app.infrastructure.models.workspace import MinistryRow

router = APIRouter(prefix="/api/preparations", tags=["Мероприятия служений"])


@router.get("")
async def preparations(session: Session, actor: CurrentActor) -> list[Record]:
    return [
        preparation_record(r)
        for r in await session.scalars(select(PreparationRow).order_by(PreparationRow.id.desc()))
        if can_read_space(actor, "ministry", r.ministry_id)
    ]


@router.post("", status_code=201)
async def create_preparation(
    data: PreparationInput, session: Session, actor: CurrentActor
) -> Record:
    if not can_write_space(actor, "ministry", data.ministry_id):
        raise PermissionError("Нет прав на подготовку мероприятия")
    if await session.get(MinistryRow, data.ministry_id) is None:
        raise LookupError("Служение не найдено")
    row = PreparationRow(
        **data.model_dump(),
        creator_id=actor.id,
        completed=[],
        steps=list(DEFAULT_PREPARATION_STEPS),
    )
    session.add(row)
    await session.commit()
    return preparation_record(row)


@router.put("/{item_id}")
async def update_preparation(
    item_id: int, data: PreparationUpdate, session: Session, actor: CurrentActor
) -> Record:
    row = await session.get(PreparationRow, item_id)
    if row is None or not can_read_space(actor, "ministry", row.ministry_id):
        raise LookupError("Мероприятие не найдено")
    if not can_write_space(actor, "ministry", row.ministry_id):
        raise PermissionError("Нет прав на подготовку мероприятия")
    if any(i < 0 or i >= len(row.steps) for i in data.completed):
        raise ValueError("Неверный шаг")
    row.completed = sorted(set(data.completed))
    await session.commit()
    return preparation_record(row)
