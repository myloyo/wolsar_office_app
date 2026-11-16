import calendar
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.types import Record
from app.infrastructure.models.planning import (
    GoalRow,
    PriorityRow,
    TemplateRow,
    WeekItemRow,
    WeekReviewRow,
    WeekStateRow,
)
from app.infrastructure.models.workspace import DepartmentRow
from app.infrastructure.weeks import SqlWeekRepository


class SqlPlanningStore:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(self, kind: str, period: str) -> list[Record]:
        if kind == "goal":
            goals = await self.session.scalars(select(GoalRow).order_by(GoalRow.id))
            return [
                {
                    "id": r.id,
                    "title": r.title,
                    "year": r.year,
                    "department_id": r.department_id,
                    "progress": r.progress,
                }
                for r in goals
                if period == "all" or r.year == int(period)
            ]
        if kind == "priority":
            priorities = await self.session.scalars(select(PriorityRow).order_by(PriorityRow.id))
            return [
                {
                    "id": r.id,
                    "title": r.title,
                    "month": r.month.isoformat()[:7],
                    "department_id": r.department_id,
                    "goal_id": r.goal_id,
                    "progress": r.progress,
                }
                for r in priorities
                if period == "all" or r.month.isoformat()[:7] == period
            ]
        return [
            {
                "id": r.id,
                "name": r.name,
                "sections": r.sections,
                "review_fields": r.review_fields,
                "approved": r.approved,
            }
            for r in await self.session.scalars(select(TemplateRow).order_by(TemplateRow.id))
        ]

    async def save(self, kind: str, item_id: int | None, data: Record) -> Record:
        values = dict(data)
        if kind != "template" and values.get("department_id") is not None:
            if await self.session.get(DepartmentRow, values["department_id"]) is None:
                raise ValueError("Отделение не найдено")
        if kind == "priority":
            values["month"] = date.fromisoformat(values["month"] + "-01")
            if values.get("goal_id"):
                goal = await self.session.get(GoalRow, values["goal_id"])
                if (
                    goal is None
                    or goal.year != values["month"].year
                    or goal.department_id not in {None, values["department_id"]}
                ):
                    raise ValueError("Годовая цель не подходит этому отделению и месяцу")
        row: GoalRow | PriorityRow | TemplateRow | None
        if kind == "goal":
            row = await self.session.get(GoalRow, item_id) if item_id else GoalRow()
        elif kind == "priority":
            row = await self.session.get(PriorityRow, item_id) if item_id else PriorityRow()
        else:
            row = await self.session.get(TemplateRow, item_id) if item_id else TemplateRow()
        if row is None:
            raise LookupError("Запись не найдена")
        for key, value in values.items():
            setattr(row, key, value)
        self.session.add(row)
        await self.session.commit()
        return next(r for r in await self.list(kind, "all") if r["id"] == row.id)

    async def report(self, month: str) -> Record:
        start = date.fromisoformat(month + "-01")
        end = start.replace(day=calendar.monthrange(start.year, start.month)[1])
        states = list(
            await self.session.scalars(
                select(WeekStateRow).where(
                    WeekStateRow.week >= start - timedelta(days=6), WeekStateRow.week <= end
                )
            )
        )
        items = list(
            await self.session.scalars(
                select(WeekItemRow).where(
                    WeekItemRow.week >= start - timedelta(days=6), WeekItemRow.week <= end
                )
            )
        )
        reviews = list(
            await self.session.scalars(
                select(WeekReviewRow).where(
                    WeekReviewRow.week >= start - timedelta(days=6), WeekReviewRow.week <= end
                )
            )
        )
        weeks = sorted(
            {r.week for r in states} | {r.week for r in items} | {r.week for r in reviews}
        )
        from dataclasses import asdict

        return {
            "month": month,
            "basis": (
                "Недели, пересекающие календарный месяц; "
                "пограничная неделя может входить в два отчёта"
            ),
            "priorities": await self.list("priority", month),
            "weeks": [
                {
                    "week": w.isoformat(),
                    "employees": [
                        asdict(e) for e in await SqlWeekRepository(self.session).overview(w)
                    ],
                }
                for w in weeks
            ],
        }
