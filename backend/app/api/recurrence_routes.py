from fastapi import APIRouter
from sqlalchemy import select

from app.api.routes import CurrentActor, Session
from app.api.schemas.recurrence import RecurrenceInput
from app.application.tasks import TaskService
from app.infrastructure.models.tasks import RecurrenceRow
from app.infrastructure.tasks import SqlTaskRepository

router = APIRouter(prefix="/api/tasks", tags=["Повторения"])


@router.get("/{task_id}/recurrence")
async def recurrence(
    task_id: int, session: Session, actor: CurrentActor
) -> dict[str, object] | None:
    await TaskService(SqlTaskRepository(session)).get_visible(actor, task_id)
    row = await session.scalar(select(RecurrenceRow).where(RecurrenceRow.task_id == task_id))
    return (
        {"frequency": row.frequency, "next_date": row.next_date, "active": row.active}
        if row
        else None
    )


@router.put("/{task_id}/recurrence")
async def save_recurrence(
    task_id: int, data: RecurrenceInput, session: Session, actor: CurrentActor
) -> dict[str, bool]:
    task = await TaskService(SqlTaskRepository(session)).get_visible(actor, task_id)
    if not task.can_edit(actor):
        raise PermissionError("Повторения настраивает постановщик")
    if data.next_date <= task.due_date:
        raise ValueError("Первое повторение должно быть позже срока исходной задачи")
    row = await session.scalar(
        select(RecurrenceRow).where(RecurrenceRow.task_id == task_id).with_for_update()
    )
    if row:
        row.frequency, row.next_date, row.active, row.anchor_day = (
            data.frequency,
            data.next_date,
            data.active,
            data.next_date.day,
        )
        row.revision += 1
    else:
        session.add(
            RecurrenceRow(
                task_id=task_id,
                frequency=data.frequency,
                next_date=data.next_date,
                anchor_day=data.next_date.day,
                active=data.active,
                revision=1,
            )
        )
    await session.commit()
    return {"ok": True}
