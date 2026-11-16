import asyncio
import json
from datetime import UTC, datetime, timedelta

from pywebpush import WebPushException, webpush
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.jobs import next_occurrence
from app.constants.calendar import SARATOV_TIMEZONE
from app.domain.calendar import is_reminder_day, week_start
from app.infrastructure.models.auth import AuthRateRow, ChallengeRow, SessionRow
from app.infrastructure.models.calendar import EventRow, SignupRow, SlotRow
from app.infrastructure.models.notifications import NotificationRow, SubscriptionRow
from app.infrastructure.models.planning import WeekItemRow, WeekStateRow
from app.infrastructure.models.tasks import OccurrenceRow, RecurrenceRow, TaskChecklistRow, TaskRow
from app.infrastructure.models.workspace import MembershipRow, UserRow
from app.infrastructure.notifications import notify
from app.infrastructure.settings import settings


async def run_jobs(session: AsyncSession, now: datetime) -> None:
    today = now.astimezone(SARATOV_TIMEZONE).date()
    recurrences = list(
        await session.scalars(
            select(RecurrenceRow).where(
                RecurrenceRow.active.is_(True), RecurrenceRow.next_date <= today
            )
        )
    )
    for recurrence in recurrences:
        claimed = await session.scalar(
            update(RecurrenceRow)
            .where(
                RecurrenceRow.id == recurrence.id,
                RecurrenceRow.revision == recurrence.revision,
                RecurrenceRow.next_date <= today,
            )
            .values(revision=RecurrenceRow.revision + 1)
            .returning(RecurrenceRow.id)
        )
        if claimed is None:
            continue
        source = await session.get(TaskRow, recurrence.task_id)
        if source is None:
            continue
        due = recurrence.next_date
        for _ in range(30):
            if due > today:
                break
            existing = await session.get(OccurrenceRow, (recurrence.id, due))
            if not existing:
                clone = TaskRow(
                    title=source.title,
                    description=source.description,
                    creator_id=source.creator_id,
                    assignee_id=source.assignee_id,
                    department_id=source.department_id,
                    due_date=due,
                    category=source.category,
                    priority=source.priority,
                    status="new",
                    coexecutor_ids=list(source.coexecutor_ids),
                    observer_ids=list(source.observer_ids),
                    result="",
                    version=1,
                )
                session.add(clone)
                await session.flush()
                items = list(
                    await session.scalars(
                        select(TaskChecklistRow).where(
                            TaskChecklistRow.task_id == source.id,
                            TaskChecklistRow.deleted.is_(False),
                        )
                    )
                )
                session.add_all(
                    [
                        TaskChecklistRow(task_id=clone.id, title=i.title, done=False, deleted=False)
                        for i in items
                    ]
                )
                session.add(OccurrenceRow(recurrence_id=recurrence.id, day=due, task_id=clone.id))
                await notify(
                    session,
                    clone.assignee_id,
                    "Создана повторяющаяся задача",
                    f"/tasks?task={clone.id}",
                    f"repeat:{recurrence.id}:{due}",
                )
            due = next_occurrence(due, recurrence.frequency, recurrence.anchor_day)
        recurrence.next_date = due
    if is_reminder_day(today):
        assignments = await session.execute(
            select(SlotRow, SignupRow, EventRow)
            .join(SignupRow, SignupRow.slot_id == SlotRow.id)
            .join(EventRow, EventRow.id == SlotRow.event_id)
            .where(
                SignupRow.status == "active",
                EventRow.cancelled.is_(False),
                EventRow.starts_at > now,
                EventRow.starts_at <= now + timedelta(days=1),
            )
        )
        for slot, signup, _event in assignments:
            if await session.get(MembershipRow, (slot.ministry_id, signup.user_id)):
                await notify(
                    session,
                    signup.user_id,
                    "Скоро ваше служение",
                    "/slots",
                    f"slot:{slot.id}:{signup.user_id}:{today}",
                )
        users = list(await session.scalars(select(UserRow).where(UserRow.active.is_(True))))
        for task in await session.scalars(
            select(TaskRow).where(
                TaskRow.status != "done", TaskRow.due_date <= today + timedelta(days=1)
            )
        ):
            title = "Задача просрочена" if task.due_date < today else "Приближается срок задачи"
            await notify(
                session,
                task.assignee_id,
                title,
                f"/tasks?task={task.id}",
                f"deadline:{task.id}:{today}",
            )
        if today.weekday() in {1, 2}:
            week = week_start(today)
            for user in users:
                if not set(user.roles) & {"office", "admin"}:
                    continue
                state = await session.get(WeekStateRow, (user.id, week))
                has_plan = await session.scalar(
                    select(WeekItemRow.id)
                    .where(WeekItemRow.user_id == user.id, WeekItemRow.week == week)
                    .limit(1)
                )
                if (today.weekday() == 2 and state is None and not has_plan) or (
                    today.weekday() == 1 and (state is None or state.closed_at is None)
                ):
                    await notify(
                        session,
                        user.id,
                        "Откройте недельный план"
                        if today.weekday() == 2
                        else "Подведите итоги и закройте неделю",
                        "/week",
                        f"week:{user.id}:{today}",
                    )
    await session.execute(delete(AuthRateRow).where(AuthRateRow.expires_at < now))
    await session.execute(
        delete(ChallengeRow).where(ChallengeRow.expires_at < now - timedelta(days=1))
    )
    await session.execute(delete(SessionRow).where(SessionRow.expires_at < now - timedelta(days=1)))
    await session.commit()


async def deliver_push(session: AsyncSession, now: datetime | None = None) -> None:
    if not settings.push_private_key or not settings.push_contact:
        return
    now = now or datetime.now(UTC)
    await session.execute(
        update(NotificationRow)
        .where(
            NotificationRow.push_state == "processing",
            NotificationRow.reserved_at < now - timedelta(minutes=10),
        )
        .values(push_state="pending")
    )
    await session.commit()
    ids = list(
        await session.scalars(
            select(NotificationRow.id)
            .where(NotificationRow.push_state == "pending", NotificationRow.attempts < 5)
            .limit(50)
        )
    )
    for notification_id in ids:
        row = await session.scalar(
            update(NotificationRow)
            .where(NotificationRow.id == notification_id, NotificationRow.push_state == "pending")
            .values(push_state="processing", reserved_at=now)
            .returning(NotificationRow)
        )
        await session.commit()
        if row is None:
            continue
        if row.dedupe_key.startswith(("deadline:", "week:")) and not is_reminder_day(
            now.astimezone(SARATOV_TIMEZONE).date()
        ):
            row.push_state = "pending"
            await session.commit()
            continue
        user = await session.get(UserRow, row.user_id)
        if user is None or not user.active:
            row.push_state = "disabled"
            await session.commit()
            continue
        subscriptions = list(
            await session.scalars(
                select(SubscriptionRow).where(SubscriptionRow.user_id == row.user_id)
            )
        )
        failed = False
        for subscription in subscriptions:
            try:
                await asyncio.to_thread(
                    webpush,
                    subscription_info={
                        "endpoint": subscription.endpoint,
                        "keys": subscription.keys,
                    },
                    data=json.dumps(
                        {"id": row.id, "title": row.title, "href": row.href}, ensure_ascii=False
                    ),
                    vapid_private_key=settings.push_private_key,
                    vapid_claims={"sub": settings.push_contact},
                    timeout=15,
                )
            except WebPushException as error:
                if error.response is not None and error.response.status_code in {404, 410}:
                    await session.delete(subscription)
                else:
                    failed = True
        row.attempts += 1
        row.push_state = (
            "pending" if failed and row.attempts < 5 else "failed" if failed else "sent"
        )
        row.reserved_at = None
        await session.commit()
