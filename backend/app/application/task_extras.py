from datetime import UTC, datetime
from typing import Protocol

from app.application.tasks import TaskService
from app.application.types import Record
from app.domain.models import Actor, Role


class ExtrasStore(Protocol):
    async def get(self, kind: str, item_id: int) -> Record: ...
    async def update(self, kind: str, item_id: int, data: Record) -> None: ...


class TaskExtrasService:
    def __init__(self, store: ExtrasStore, tasks: TaskService) -> None:
        self.store, self.tasks = store, tasks

    async def change(
        self, actor: Actor, task_id: int, kind: str, item_id: int, data: Record
    ) -> None:
        task = await self.tasks.get_visible(actor, task_id)
        row = await self.store.get(kind, item_id)
        if row["task_id"] != task_id:
            raise LookupError("Элемент задачи не найден")
        if kind == "comment":
            if actor.id != row["author_id"] and Role.ADMIN not in actor.roles:
                raise PermissionError("Комментарий изменяет автор или администратор")
            if "text" in data:
                data["edited_at"] = datetime.now(UTC)
        elif not task.can_contribute(actor):
            raise PermissionError("Нет прав на чек-лист")
        await self.store.update(kind, item_id, data)
