from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy import (
    text as sql_text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.models.base import Base


class TaskRow(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(240))
    description: Mapped[str] = mapped_column(Text, default="")
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    assignee_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    due_date: Mapped[date] = mapped_column(Date)
    category: Mapped[str] = mapped_column(String(40))
    priority: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="new")
    coexecutor_ids: Mapped[list[int]] = mapped_column(
        JSON, default=list, server_default=sql_text("'[]'")
    )
    observer_ids: Mapped[list[int]] = mapped_column(
        JSON, default=list, server_default=sql_text("'[]'")
    )
    result: Mapped[str] = mapped_column(Text, default="", server_default="")
    version: Mapped[int] = mapped_column(default=1, server_default="1")


class TaskCommentRow(Base):
    __tablename__ = "task_comments"
    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    deleted: Mapped[bool] = mapped_column(Boolean, default=False, server_default=sql_text("false"))
    edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TaskChecklistRow(Base):
    __tablename__ = "task_checklist"
    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), index=True)
    title: Mapped[str] = mapped_column(String(240))
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted: Mapped[bool] = mapped_column(Boolean, default=False, server_default=sql_text("false"))


class RecurrenceRow(Base):
    __tablename__ = "task_recurrences"
    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), unique=True)
    frequency: Mapped[str] = mapped_column(String(20))
    next_date: Mapped[date] = mapped_column(Date)
    anchor_day: Mapped[int]
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    revision: Mapped[int] = mapped_column(default=1)


class OccurrenceRow(Base):
    __tablename__ = "task_occurrences"
    recurrence_id: Mapped[int] = mapped_column(ForeignKey("task_recurrences.id"), primary_key=True)
    day: Mapped[date] = mapped_column(Date, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
