from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.models.base import Base


class WeekStateRow(Base):
    __tablename__ = "week_states"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    week: Mapped[date] = mapped_column(Date, primary_key=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revision: Mapped[int] = mapped_column(default=1, server_default="1")
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    planned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class WeekItemRow(Base):
    __tablename__ = "week_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    week: Mapped[date] = mapped_column(Date)
    title: Mapped[str] = mapped_column(String(240))
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id"))
    priority_id: Mapped[int | None] = mapped_column(ForeignKey("priorities.id"))
    section: Mapped[str] = mapped_column(String(80), default="main", server_default="main")
    carried_from_id: Mapped[int | None] = mapped_column(ForeignKey("week_items.id"))
    __table_args__ = (UniqueConstraint("user_id", "week", "carried_from_id", name="uq_week_carry"),)


class WeekReviewRow(Base):
    __tablename__ = "week_reviews"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    week: Mapped[date] = mapped_column(Date, primary_key=True)
    text: Mapped[str] = mapped_column(Text)


class GoalRow(Base):
    __tablename__ = "goals"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(240))
    year: Mapped[int]
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    progress: Mapped[int] = mapped_column(default=0)


class PriorityRow(Base):
    __tablename__ = "priorities"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(240))
    month: Mapped[date] = mapped_column(Date)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    goal_id: Mapped[int | None] = mapped_column(ForeignKey("goals.id"))
    progress: Mapped[int] = mapped_column(default=0)


class TemplateRow(Base):
    __tablename__ = "week_templates"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    sections: Mapped[list[str]] = mapped_column(JSON)
    review_fields: Mapped[list[str]] = mapped_column(JSON)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
