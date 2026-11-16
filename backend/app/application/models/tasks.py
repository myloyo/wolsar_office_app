from dataclasses import dataclass
from datetime import date, datetime

from app.domain.models import TaskStatus
from app.domain.tasks import Task


@dataclass
class TaskChanges:
    title: str | None = None
    description: str | None = None
    assignee_id: int | None = None
    department_id: int | None = None
    due_date: date | None = None
    category: str | None = None
    priority: str | None = None
    coexecutor_ids: list[int] | None = None
    observer_ids: list[int] | None = None
    result: str | None = None
    status: TaskStatus | None = None
    expected_version: int | None = None


@dataclass
class Comment:
    id: int
    task_id: int
    author_id: int
    text: str
    created_at: datetime
    deleted: bool = False
    edited_at: datetime | None = None


@dataclass
class ChecklistItem:
    id: int
    task_id: int
    title: str
    done: bool
    deleted: bool = False


@dataclass
class TaskDetail:
    task: Task
    comments: list[Comment]
    checklist: list[ChecklistItem]
    can_edit: bool
    can_contribute: bool
