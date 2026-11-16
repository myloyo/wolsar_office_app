from dataclasses import asdict
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.models.tasks import ChecklistItem, Comment
from app.domain.exceptions import ConflictError
from app.domain.tasks import Task
from app.infrastructure.mappers.tasks import to_task
from app.infrastructure.models.tasks import TaskChecklistRow, TaskCommentRow, TaskRow
from app.infrastructure.models.workspace import DepartmentRow, UserRow
from app.infrastructure.notifications import notify


class SqlTaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_all(self) -> list[Task]:
        rows = await self.session.scalars(select(TaskRow).order_by(TaskRow.id.desc()))
        return [to_task(row) for row in rows]

    async def get(self, task_id: int) -> Task | None:
        row = await self.session.get(TaskRow, task_id)
        return to_task(row) if row else None

    async def save(self, task: Task) -> Task:
        created = task.id == 0
        values = asdict(task)
        if task.id == 0:
            values.pop("id")
            row = TaskRow(**values)
            self.session.add(row)
        else:
            values.pop("id")
            values["version"] = task.version + 1
            changed_id = await self.session.scalar(
                update(TaskRow)
                .where(TaskRow.id == task.id, TaskRow.version == task.version)
                .values(**values)
                .returning(TaskRow.id)
            )
            if changed_id is None:
                await self.session.rollback()
                raise ConflictError("Задача уже изменена. Обновите карточку.")
            existing = await self.session.get(TaskRow, task.id, populate_existing=True)
            assert existing is not None
            row = existing
        await self.session.flush()
        for recipient in {row.creator_id, row.assignee_id, *row.coexecutor_ids, *row.observer_ids}:
            await notify(
                self.session,
                recipient,
                "Вам назначена задача" if created else "Задача обновлена",
                f"/tasks?task={row.id}",
            )
        await self.session.commit()
        await self.session.refresh(row)
        return to_task(row)

    async def validate_references(self, task: Task) -> None:
        if await self.session.get(DepartmentRow, task.department_id) is None:
            raise ValueError("Отделение не найдено")
        ids = {task.assignee_id, *task.coexecutor_ids, *task.observer_ids}
        existing = set(await self.session.scalars(select(UserRow.id).where(UserRow.id.in_(ids))))
        if ids != existing:
            raise ValueError("Один из участников не найден")

    async def comments(self, task_id: int) -> list[Comment]:
        rows = await self.session.scalars(
            select(TaskCommentRow)
            .where(TaskCommentRow.task_id == task_id)
            .order_by(TaskCommentRow.created_at, TaskCommentRow.id)
        )
        return [
            Comment(
                r.id,
                r.task_id,
                r.author_id,
                "Комментарий удалён" if r.deleted else r.text,
                r.created_at.replace(tzinfo=UTC) if r.created_at.tzinfo is None else r.created_at,
                r.deleted,
                r.edited_at,
            )
            for r in rows
        ]

    async def add_comment(self, task_id: int, author_id: int, text: str) -> Comment:
        row = TaskCommentRow(
            task_id=task_id, author_id=author_id, text=text, created_at=datetime.now(UTC)
        )
        self.session.add(row)
        task = await self.session.get(TaskRow, task_id)
        if task:
            for recipient in {
                task.creator_id,
                task.assignee_id,
                *task.coexecutor_ids,
                *task.observer_ids,
            } - {author_id}:
                await notify(
                    self.session, recipient, "Новый комментарий в задаче", f"/tasks?task={task_id}"
                )
        await self.session.commit()
        await self.session.refresh(row)
        return Comment(row.id, task_id, author_id, text, row.created_at.replace(tzinfo=UTC))

    async def checklist(self, task_id: int) -> list[ChecklistItem]:
        rows = await self.session.scalars(
            select(TaskChecklistRow)
            .where(TaskChecklistRow.task_id == task_id)
            .order_by(TaskChecklistRow.id)
        )
        return [ChecklistItem(r.id, r.task_id, r.title, r.done, r.deleted) for r in rows]

    async def add_checklist_item(self, task_id: int, title: str) -> ChecklistItem:
        row = TaskChecklistRow(task_id=task_id, title=title, done=False)
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return ChecklistItem(row.id, task_id, title, row.done)

    async def toggle_checklist_item(self, task_id: int, item_id: int, done: bool) -> ChecklistItem:
        row = await self.session.get(TaskChecklistRow, item_id)
        if row is None or row.task_id != task_id or row.deleted:
            raise LookupError("Пункт чек-листа не найден")
        row.done = done
        await self.session.commit()
        return ChecklistItem(row.id, task_id, row.title, done)
