import calendar
from datetime import date, datetime, timedelta
from typing import Protocol

from app.application.models.weeks import EmployeeWeek, WeekItem, WeekPlan
from app.constants.calendar import SARATOV_TIMEZONE
from app.domain.calendar import week_start
from app.domain.exceptions import ConflictError
from app.domain.models import Actor, Role
from app.domain.tasks import Task


def plan_is_late(
    week: date, planned_at: datetime | None, has_items: bool, now: datetime
) -> bool | None:
    if planned_at is not None:
        return planned_at.astimezone(SARATOV_TIMEZONE).date() > week
    if has_items:
        return None  # legacy plans have no reliable timestamp
    return now.astimezone(SARATOV_TIMEZONE).date() > week


class WeekRepository(Protocol):
    async def get(self, user_id: int, week: date) -> WeekPlan: ...
    async def add(
        self,
        user_id: int,
        week: date,
        title: str,
        task_id: int | None,
        priority_id: int | None,
        section: str,
    ) -> WeekItem: ...
    async def references(
        self, task_id: int | None, priority_id: int | None
    ) -> tuple[Task | None, tuple[int, date] | None]: ...
    async def toggle(self, user_id: int, week: date, item_id: int, done: bool) -> WeekItem: ...
    async def save_review(self, user_id: int, week: date, text: str) -> None: ...
    async def open(self, user_id: int, week: date) -> None: ...
    async def close(self, user_id: int, week: date) -> None: ...
    async def reopen(self, user_id: int, week: date) -> None: ...
    async def overview(self, week: date) -> list[EmployeeWeek]: ...


class WeekService:
    def __init__(self, repository: WeekRepository, today: date) -> None:
        self.repository = repository
        self.week = week_start(today)

    @staticmethod
    def require_office(actor: Actor) -> None:
        if not actor.roles.intersection({Role.ADMIN, Role.OFFICE}):
            raise PermissionError("Недельное планирование доступно сотрудникам офиса")

    async def get(self, actor: Actor) -> WeekPlan:
        self.require_office(actor)
        return await self.repository.get(actor.id, self.week)

    async def open(self, actor: Actor) -> WeekPlan:
        self.require_office(actor)
        await self.repository.open(actor.id, self.week)
        return await self.get(actor)

    async def close(self, actor: Actor) -> WeekPlan:
        self.require_office(actor)
        plan = await self.get(actor)
        if not plan.items or not plan.review.strip():
            raise ConflictError("Для закрытия добавьте план и сохраните итоги недели.")
        await self.repository.close(actor.id, self.week)
        return await self.get(actor)

    async def reopen(self, actor: Actor) -> WeekPlan:
        self.require_office(actor)
        await self.repository.reopen(actor.id, self.week)
        return await self.get(actor)

    async def overview(self, actor: Actor) -> list[EmployeeWeek]:
        if Role.ADMIN not in actor.roles:
            raise PermissionError("Обзор планов доступен только администратору")
        return await self.repository.overview(self.week)

    async def add(
        self,
        actor: Actor,
        title: str,
        task_id: int | None = None,
        priority_id: int | None = None,
        section: str = "main",
    ) -> WeekItem:
        self.require_office(actor)
        task, priority = await self.repository.references(task_id, priority_id)
        if task_id is not None and (task is None or not task.can_read(actor)):
            raise ValueError("Связанная задача недоступна")
        if priority_id is not None:
            if priority is None:
                raise ValueError("Приоритет не найден")
            department_id, month = priority
            month_end = month.replace(day=calendar.monthrange(month.year, month.month)[1])
            if (
                (Role.ADMIN not in actor.roles and department_id not in actor.department_ids)
                or month > self.week + timedelta(days=6)
                or month_end < self.week
            ):
                raise ValueError("Приоритет не подходит этой неделе или отделению")
        return await self.repository.add(actor.id, self.week, title, task_id, priority_id, section)

    async def toggle(self, actor: Actor, item_id: int, done: bool) -> WeekItem:
        self.require_office(actor)
        return await self.repository.toggle(actor.id, self.week, item_id, done)

    async def save_review(self, actor: Actor, text: str) -> None:
        self.require_office(actor)
        await self.repository.save_review(actor.id, self.week, text)
