from datetime import date, datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.models import TaskStatus


class TaskInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=240, pattern=r"\S")
    description: str = Field(default="", max_length=10000)
    assignee_id: int
    department_id: int
    due_date: date
    category: Literal["personal", "leaders", "responsible", "information", "ideas"] = "personal"
    priority: Literal["normal", "high"] = "normal"
    coexecutor_ids: list[int] = Field(default_factory=list, max_length=100)
    observer_ids: list[int] = Field(default_factory=list, max_length=100)


class TaskOutput(TaskInput):
    id: int
    creator_id: int
    status: TaskStatus
    result: str
    version: int


class TaskPatch(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str | None = Field(default=None, min_length=1, max_length=240)
    description: str | None = Field(default=None, max_length=10000)
    assignee_id: int | None = Field(default=None, gt=0)
    department_id: int | None = Field(default=None, gt=0)
    due_date: date | None = None
    category: Literal["personal", "leaders", "responsible", "information", "ideas"] | None = None
    priority: Literal["normal", "high"] | None = None
    coexecutor_ids: list[int] | None = Field(default=None, max_length=100)
    observer_ids: list[int] | None = Field(default=None, max_length=100)
    result: str | None = Field(default=None, max_length=10000)
    status: TaskStatus | None = None
    expected_version: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def nonempty_changes(self) -> Self:
        if not self.model_fields_set - {"expected_version"}:
            raise ValueError("Укажите изменяемое поле")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Поля задачи не могут быть null")
        return self


class CommentInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    text: str = Field(min_length=1, max_length=10000)


class CommentOutput(BaseModel):
    id: int
    task_id: int
    author_id: int
    text: str
    created_at: datetime
    deleted: bool = False
    edited_at: datetime | None = None


class ChecklistOutput(BaseModel):
    id: int
    task_id: int
    title: str
    done: bool
    deleted: bool = False


class TaskDetailOutput(BaseModel):
    task: TaskOutput
    comments: list[CommentOutput]
    checklist: list[ChecklistOutput]
    can_edit: bool
    can_contribute: bool
