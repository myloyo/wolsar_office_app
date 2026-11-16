from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.models.weeks import EmployeeWeek, WeekItem, WeekPlan
from app.application.weeks import plan_is_late
from app.domain.exceptions import ConflictError
from app.domain.tasks import Task
from app.infrastructure.mappers.tasks import to_task
from app.infrastructure.mappers.weeks import to_item
from app.infrastructure.models.planning import PriorityRow, WeekItemRow, WeekReviewRow, WeekStateRow
from app.infrastructure.models.tasks import TaskRow
from app.infrastructure.models.workspace import UserRow
from app.utils.dates import aware


class SqlWeekRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: int, week: date) -> WeekPlan:
        items = await self.session.scalars(
            select(WeekItemRow)
            .where(WeekItemRow.user_id == user_id, WeekItemRow.week == week)
            .order_by(WeekItemRow.id)
        )
        review = await self.session.get(WeekReviewRow, (user_id, week))
        state = await self.session.get(WeekStateRow, (user_id, week))
        item_list = [to_item(i) for i in items]
        closed = state.closed_at if state else None
        if closed is not None and closed.tzinfo is None:
            closed = closed.replace(tzinfo=UTC)
        return WeekPlan(
            week,
            item_list,
            review.text if review else "",
            bool(state or item_list or review),
            closed,
            aware(state.opened_at) if state and state.opened_at else None,
            aware(state.planned_at) if state and state.planned_at else None,
            plan_is_late(
                week,
                aware(state.planned_at) if state and state.planned_at else None,
                bool(item_list),
                datetime.now(UTC),
            ),
        )

    async def ensure_week_state(self, user_id: int, week: date) -> WeekStateRow:
        state = await self.session.get(WeekStateRow, (user_id, week), populate_existing=True)
        if state is None:
            state = WeekStateRow(
                user_id=user_id, week=week, closed_at=None, opened_at=datetime.now(UTC)
            )
            self.session.add(state)
            try:
                await self.session.flush()
                pending = list(
                    await self.session.scalars(
                        select(WeekItemRow).where(
                            WeekItemRow.user_id == user_id,
                            WeekItemRow.week == week - timedelta(days=7),
                            WeekItemRow.done.is_(False),
                        )
                    )
                )
                self.session.add_all(
                    [
                        WeekItemRow(
                            user_id=user_id,
                            week=week,
                            title=item.title,
                            done=False,
                            task_id=item.task_id,
                            priority_id=None,
                            section=item.section,
                            carried_from_id=item.id,
                        )
                        for item in pending
                    ]
                )
                if pending:
                    state.planned_at = datetime.now(UTC)
                await self.session.flush()
            except IntegrityError as error:
                await self.session.rollback()
                raise ConflictError("План уже обновлён. Повторите действие.") from error
        return state

    async def require_open_week(self, user_id: int, week: date) -> None:
        await self.ensure_week_state(user_id, week)
        changed = await self.session.scalar(
            update(WeekStateRow)
            .where(
                WeekStateRow.user_id == user_id,
                WeekStateRow.week == week,
                WeekStateRow.closed_at.is_(None),
            )
            .values(revision=WeekStateRow.revision + 1)
            .returning(WeekStateRow.user_id)
        )
        if changed is None:
            await self.session.rollback()
            raise ConflictError("Неделя закрыта. Сначала возобновите её.")

    async def open(self, user_id: int, week: date) -> None:
        state = await self.ensure_week_state(user_id, week)
        if state.closed_at is not None:
            raise ConflictError("Неделя уже закрыта. Используйте возобновление.")
        await self.session.commit()

    async def close(self, user_id: int, week: date) -> None:
        await self.require_open_week(user_id, week)
        await self.session.execute(
            update(WeekStateRow)
            .where(WeekStateRow.user_id == user_id, WeekStateRow.week == week)
            .values(closed_at=datetime.now(UTC))
        )
        await self.session.commit()

    async def reopen(self, user_id: int, week: date) -> None:
        state = await self.session.get(WeekStateRow, (user_id, week))
        if state is None:
            raise ConflictError("Сначала откройте неделю.")
        await self.session.execute(
            update(WeekStateRow)
            .where(WeekStateRow.user_id == user_id, WeekStateRow.week == week)
            .values(closed_at=None, revision=WeekStateRow.revision + 1)
        )
        await self.session.commit()

    async def references(
        self, task_id: int | None, priority_id: int | None
    ) -> tuple[Task | None, tuple[int, date] | None]:
        task = await self.session.get(TaskRow, task_id) if task_id else None
        priority = await self.session.get(PriorityRow, priority_id) if priority_id else None
        return to_task(task) if task else None, (
            priority.department_id,
            priority.month,
        ) if priority else None

    async def add(
        self,
        user_id: int,
        week: date,
        title: str,
        task_id: int | None = None,
        priority_id: int | None = None,
        section: str = "main",
    ) -> WeekItem:
        await self.require_open_week(user_id, week)
        item = WeekItemRow(
            user_id=user_id,
            week=week,
            title=title,
            task_id=task_id,
            priority_id=priority_id,
            section=section,
        )
        await self.session.execute(
            update(WeekStateRow)
            .where(
                WeekStateRow.user_id == user_id,
                WeekStateRow.week == week,
                WeekStateRow.planned_at.is_(None),
            )
            .values(planned_at=datetime.now(UTC))
        )
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return to_item(item)

    async def toggle(self, user_id: int, week: date, item_id: int, done: bool) -> WeekItem:
        item = await self.session.get(WeekItemRow, item_id)
        if item is None or item.user_id != user_id or item.week != week:
            raise LookupError("Пункт плана не найден")
        await self.require_open_week(user_id, week)
        item.done = done
        await self.session.commit()
        return to_item(item)

    async def save_review(self, user_id: int, week: date, text: str) -> None:
        await self.require_open_week(user_id, week)
        review = await self.session.get(WeekReviewRow, (user_id, week))
        if review is None:
            self.session.add(WeekReviewRow(user_id=user_id, week=week, text=text))
        else:
            review.text = text
        await self.session.commit()

    async def overview(self, week: date) -> list[EmployeeWeek]:
        users = await self.session.scalars(
            select(UserRow).where(UserRow.active.is_(True)).order_by(UserRow.id)
        )
        # A single query per data type keeps the overview independent of staff count.
        items = list(
            await self.session.scalars(select(WeekItemRow).where(WeekItemRow.week == week))
        )
        reviews = {
            r.user_id: r.text
            for r in await self.session.scalars(
                select(WeekReviewRow).where(WeekReviewRow.week == week)
            )
        }
        states = {
            s.user_id: s
            for s in await self.session.scalars(
                select(WeekStateRow).where(WeekStateRow.week == week)
            )
        }
        result = []
        for user in users:
            if not set(user.roles).intersection({"office", "admin"}):
                continue
            own = [to_item(item) for item in items if item.user_id == user.id]
            state = states.get(user.id)
            closed = state.closed_at if state else None
            if closed is not None and closed.tzinfo is None:
                closed = closed.replace(tzinfo=UTC)
            result.append(
                EmployeeWeek(
                    user.id,
                    user.name,
                    user.department_ids,
                    WeekPlan(
                        week,
                        own,
                        reviews.get(user.id, ""),
                        bool(state or own or user.id in reviews),
                        closed,
                        aware(state.opened_at) if state and state.opened_at else None,
                        aware(state.planned_at) if state and state.planned_at else None,
                        plan_is_late(
                            week,
                            aware(state.planned_at) if state and state.planned_at else None,
                            bool(own),
                            datetime.now(UTC),
                        ),
                    ),
                )
            )
        return result
