from dataclasses import asdict
from datetime import datetime

from fastapi import APIRouter
from sqlalchemy import select

from app.api.routes import CurrentActor, Session
from app.application.tasks import TaskService
from app.application.types import Record
from app.constants.calendar import SARATOV_TIMEZONE
from app.domain.calendar import week_start
from app.domain.models import Role
from app.infrastructure.models.workspace import MembershipRow, UserRow
from app.infrastructure.tasks import SqlTaskRepository
from app.infrastructure.weeks import SqlWeekRepository

router = APIRouter(prefix="/api/people", tags=["Сотрудники"])


@router.get("/{user_id}")
async def person(user_id: int, session: Session, actor: CurrentActor) -> Record:
    user = await session.get(UserRow, user_id)
    memberships = set(
        await session.scalars(
            select(MembershipRow.ministry_id).where(MembershipRow.user_id == user_id)
        )
    )
    if (
        user is None
        or not user.active
        or (
            actor.id != user_id
            and Role.ADMIN not in actor.roles
            and not actor.department_ids.intersection(user.department_ids)
            and not actor.ministry_ids.intersection(memberships)
        )
    ):
        raise LookupError("Сотрудник не найден")
    tasks = [
        asdict(t)
        for t in await TaskService(SqlTaskRepository(session)).list_visible(actor)
        if user_id in [t.assignee_id, *t.coexecutor_ids]
    ]
    plan = None
    if actor.id == user_id or Role.ADMIN in actor.roles:
        plan = asdict(
            await SqlWeekRepository(session).get(
                user_id, week_start(datetime.now(SARATOV_TIMEZONE).date())
            )
        )
    return {
        "id": user.id,
        "name": user.name,
        "roles": user.roles,
        "department_ids": user.department_ids,
        "tasks": tasks,
        "plan": plan,
    }
