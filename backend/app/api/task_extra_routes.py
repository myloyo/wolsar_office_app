from fastapi import APIRouter

from app.api.routes import CurrentActor, Session
from app.api.schemas.task_extra import ChecklistEdit, CommentEdit
from app.application.task_extras import TaskExtrasService
from app.application.tasks import TaskService
from app.infrastructure.task_extras import SqlExtrasStore
from app.infrastructure.tasks import SqlTaskRepository

router = APIRouter(prefix="/api/tasks", tags=["Обсуждения"])


def service(session: Session) -> TaskExtrasService:
    return TaskExtrasService(SqlExtrasStore(session), TaskService(SqlTaskRepository(session)))


@router.put("/{task_id}/comments/{item_id}")
async def edit_comment(
    task_id: int, item_id: int, data: CommentEdit, session: Session, actor: CurrentActor
) -> dict[str, bool]:
    await service(session).change(actor, task_id, "comment", item_id, data.model_dump())
    return {"ok": True}


@router.delete("/{task_id}/comments/{item_id}")
async def delete_comment(
    task_id: int, item_id: int, session: Session, actor: CurrentActor
) -> dict[str, bool]:
    await service(session).change(actor, task_id, "comment", item_id, {"deleted": True})
    return {"ok": True}


@router.post("/{task_id}/comments/{item_id}/restore")
async def restore_comment(
    task_id: int, item_id: int, session: Session, actor: CurrentActor
) -> dict[str, bool]:
    await service(session).change(actor, task_id, "comment", item_id, {"deleted": False})
    return {"ok": True}


@router.put("/{task_id}/checklist/{item_id}")
async def edit_item(
    task_id: int, item_id: int, data: ChecklistEdit, session: Session, actor: CurrentActor
) -> dict[str, bool]:
    await service(session).change(actor, task_id, "checklist", item_id, data.model_dump())
    return {"ok": True}


@router.delete("/{task_id}/checklist/{item_id}")
async def delete_item(
    task_id: int, item_id: int, session: Session, actor: CurrentActor
) -> dict[str, bool]:
    await service(session).change(actor, task_id, "checklist", item_id, {"deleted": True})
    return {"ok": True}


@router.post("/{task_id}/checklist/{item_id}/restore")
async def restore_item(
    task_id: int, item_id: int, session: Session, actor: CurrentActor
) -> dict[str, bool]:
    await service(session).change(actor, task_id, "checklist", item_id, {"deleted": False})
    return {"ok": True}
