from dataclasses import dataclass, field
from datetime import date

from app.domain.access import can_access_task
from app.domain.models import Actor, Role, TaskStatus


@dataclass
class Task:
    id: int
    title: str
    description: str
    creator_id: int
    assignee_id: int
    department_id: int
    due_date: date
    category: str
    priority: str
    status: TaskStatus
    coexecutor_ids: list[int] = field(default_factory=list)
    observer_ids: list[int] = field(default_factory=list)
    result: str = ""
    version: int = 1

    def can_read(self, actor: Actor) -> bool:
        return can_access_task(
            actor,
            self.creator_id,
            self.assignee_id,
            self.department_id,
            tuple(self.coexecutor_ids),
            tuple(self.observer_ids),
        )

    def can_edit(self, actor: Actor) -> bool:
        return Role.ADMIN in actor.roles or actor.id == self.creator_id

    def can_contribute(self, actor: Actor) -> bool:
        return self.can_edit(actor) or actor.id in [self.assignee_id, *self.coexecutor_ids]

    def validate_participants(self) -> None:
        if len(self.coexecutor_ids) != len(set(self.coexecutor_ids)) or len(
            self.observer_ids
        ) != len(set(self.observer_ids)):
            raise ValueError("Список участников не должен содержать повторов")
        if self.assignee_id in self.coexecutor_ids or self.assignee_id in self.observer_ids:
            raise ValueError("Исполнителя не нужно дублировать в других ролях задачи")
        if set(self.coexecutor_ids) & set(self.observer_ids):
            raise ValueError("Участник не может быть одновременно соисполнителем и наблюдателем")
