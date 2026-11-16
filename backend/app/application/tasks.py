from typing import Protocol

from app.application.models.tasks import ChecklistItem, Comment, TaskChanges, TaskDetail
from app.domain.exceptions import ConflictError
from app.domain.models import Actor, Role, TaskStatus
from app.domain.tasks import Task


class TaskRepository(Protocol):
    async def list_all(self) -> list[Task]: ...
    async def get(self, task_id: int) -> Task | None: ...
    async def save(self, task: Task) -> Task: ...
    async def validate_references(self, task: Task) -> None: ...
    async def comments(self, task_id: int) -> list[Comment]: ...
    async def add_comment(self, task_id: int, author_id: int, text: str) -> Comment: ...
    async def checklist(self, task_id: int) -> list[ChecklistItem]: ...
    async def add_checklist_item(self, task_id: int, title: str) -> ChecklistItem: ...
    async def toggle_checklist_item(
        self, task_id: int, item_id: int, done: bool
    ) -> ChecklistItem: ...


class TaskService:
    def __init__(self, repository: TaskRepository) -> None:
        self.repository = repository

    async def list_visible(self, actor: Actor) -> list[Task]:
        return [task for task in await self.repository.list_all() if task.can_read(actor)]

    async def get_visible(self, actor: Actor, task_id: int) -> Task:
        task = await self.repository.get(task_id)
        if task is None or not task.can_read(actor):
            raise LookupError("Задача не найдена")
        return task

    async def detail(self, actor: Actor, task_id: int) -> TaskDetail:
        task = await self.get_visible(actor, task_id)
        return TaskDetail(
            task,
            await self.repository.comments(task_id),
            await self.repository.checklist(task_id),
            task.can_edit(actor),
            task.can_contribute(actor),
        )

    async def create(self, actor: Actor, task: Task) -> Task:
        if not actor.roles.intersection({Role.ADMIN, Role.OFFICE, Role.LEADER}):
            raise PermissionError("Создание задач для этой роли недоступно")
        task.creator_id = actor.id
        task.validate_participants()
        await self.repository.validate_references(task)
        return await self.repository.save(task)

    async def update(self, actor: Actor, task_id: int, changes: TaskChanges) -> Task:
        task = await self.get_visible(actor, task_id)
        structural = (
            "title",
            "description",
            "assignee_id",
            "department_id",
            "due_date",
            "category",
            "priority",
            "coexecutor_ids",
            "observer_ids",
        )
        if any(getattr(changes, key) is not None for key in structural) and not task.can_edit(
            actor
        ):
            raise PermissionError("Изменять условия задачи может постановщик или администратор")
        if not task.can_contribute(actor):
            raise PermissionError("Задача доступна только для просмотра")
        if changes.expected_version is not None and changes.expected_version != task.version:
            raise ConflictError("Задача уже изменена. Обновите карточку и повторите действие.")
        for key in (*structural, "result", "status"):
            value = getattr(changes, key)
            if value is not None:
                setattr(task, key, value)
        task.validate_participants()
        await self.repository.validate_references(task)
        return await self.repository.save(task)

    async def change_status(self, actor: Actor, task_id: int, status: TaskStatus) -> Task:
        return await self.update(actor, task_id, TaskChanges(status=status))

    async def add_comment(self, actor: Actor, task_id: int, text: str) -> Comment:
        task = await self.get_visible(actor, task_id)
        if not task.can_contribute(actor):
            raise PermissionError("Комментировать могут участники выполнения задачи")
        return await self.repository.add_comment(task_id, actor.id, text.strip())

    async def add_checklist_item(self, actor: Actor, task_id: int, title: str) -> ChecklistItem:
        task = await self.get_visible(actor, task_id)
        if not task.can_contribute(actor):
            raise PermissionError("Изменять чек-лист могут участники выполнения задачи")
        return await self.repository.add_checklist_item(task_id, title.strip())

    async def toggle_checklist_item(
        self, actor: Actor, task_id: int, item_id: int, done: bool
    ) -> ChecklistItem:
        task = await self.get_visible(actor, task_id)
        if not task.can_contribute(actor):
            raise PermissionError("Изменять чек-лист могут участники выполнения задачи")
        return await self.repository.toggle_checklist_item(task_id, item_id, done)
