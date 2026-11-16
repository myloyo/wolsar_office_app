from sqlalchemy.ext.asyncio import AsyncSession

from app.application.types import Record
from app.infrastructure.models.tasks import TaskChecklistRow, TaskCommentRow


class SqlExtrasStore:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, kind: str, item_id: int) -> Record:
        row: TaskCommentRow | TaskChecklistRow | None
        if kind == "comment":
            row = await self.session.get(TaskCommentRow, item_id)
        else:
            row = await self.session.get(TaskChecklistRow, item_id)
        if row is None:
            raise LookupError("Элемент задачи не найден")
        return {
            "id": row.id,
            "task_id": row.task_id,
            "author_id": getattr(row, "author_id", None),
            "deleted": row.deleted,
        }

    async def update(self, kind: str, item_id: int, data: Record) -> None:
        row: TaskCommentRow | TaskChecklistRow | None
        if kind == "comment":
            row = await self.session.get(TaskCommentRow, item_id)
        else:
            row = await self.session.get(TaskChecklistRow, item_id)
        if row is None:
            raise LookupError("Элемент задачи не найден")
        for key, value in data.items():
            setattr(row, key, value)
        await self.session.commit()
