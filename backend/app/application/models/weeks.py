from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class WeekItem:
    id: int
    title: str
    done: bool
    task_id: int | None = None
    priority_id: int | None = None
    section: str = "main"
    carried_from_id: int | None = None


@dataclass
class WeekPlan:
    week: date
    items: list[WeekItem]
    review: str
    opened: bool = False
    closed_at: datetime | None = None
    opened_at: datetime | None = None
    planned_at: datetime | None = None
    late: bool | None = None


@dataclass
class EmployeeWeek:
    user_id: int
    name: str
    department_ids: list[int]
    plan: WeekPlan
