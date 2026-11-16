from collections.abc import AsyncIterator
from dataclasses import asdict
from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.tasks import (
    ChecklistOutput,
    CommentInput,
    CommentOutput,
    TaskDetailOutput,
    TaskInput,
    TaskOutput,
    TaskPatch,
)
from app.api.schemas.weeks import DoneInput, ReviewInput, WeekInput, WeekItemInput, WeekOutput
from app.application.models.tasks import TaskChanges
from app.application.models.weeks import WeekItem
from app.application.tasks import TaskService
from app.application.weeks import WeekService
from app.constants.auth import SESSION_COOKIE
from app.constants.calendar import SARATOV_TIMEZONE
from app.domain.calendar import week_start
from app.domain.models import Actor, TaskStatus
from app.domain.tasks import Task
from app.infrastructure.database import sessions
from app.infrastructure.models.workspace import DepartmentRow, UserRow
from app.infrastructure.security import actor_for, session_user
from app.infrastructure.settings import settings
from app.infrastructure.tasks import SqlTaskRepository
from app.infrastructure.weeks import SqlWeekRepository

router = APIRouter(prefix="/api")


async def session_dependency() -> AsyncIterator[AsyncSession]:
    async with sessions() as session:
        yield session


Session = Annotated[AsyncSession, Depends(session_dependency)]


async def actor_dependency(
    request: Request, session: Session, x_demo_user: Annotated[int | None, Header()] = None
) -> Actor:
    if request.cookies.get(SESSION_COOKIE) or not settings.demo_mode:
        session_account, _ = await session_user(request, session)
        return await actor_for(session, session_account)
    user = await session.get(UserRow, x_demo_user or 1)
    if user is None or not user.active:
        raise HTTPException(401, "Пользователь не найден")
    return await actor_for(session, user)


CurrentActor = Annotated[Actor, Depends(actor_dependency)]


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "mode": "demo" if settings.demo_mode else "unconfigured"}


@router.get("/bootstrap")
async def bootstrap(request: Request, session: Session, actor: CurrentActor) -> dict[str, object]:
    users = (await session.scalars(select(UserRow))).all()
    departments = (await session.scalars(select(DepartmentRow))).all()
    return {
        "demo": settings.demo_mode and not bool(request.cookies.get(SESSION_COOKIE)),
        "current_user_id": actor.id,
        "users": [
            {
                "id": u.id,
                "name": u.name,
                "roles": list(actor.roles) if u.id == actor.id else u.roles,
                "department_ids": u.department_ids,
            }
            for u in users
            if u.active
        ],
        "departments": [
            {"id": d.id, "name": d.name, "leader": d.leader, "description": d.description}
            for d in departments
        ],
        "ministry_ids": list(actor.ministry_ids),
        "led_ministry_ids": list(actor.led_ministry_ids),
    }


@router.get("/tasks", response_model=list[TaskOutput])
async def list_tasks(session: Session, actor: CurrentActor) -> list[dict[str, object]]:
    return [asdict(t) for t in await TaskService(SqlTaskRepository(session)).list_visible(actor)]


@router.post("/tasks", response_model=TaskOutput, status_code=201)
async def create_task(data: TaskInput, session: Session, actor: CurrentActor) -> dict[str, object]:
    task = Task(id=0, creator_id=actor.id, status=TaskStatus.NEW, **data.model_dump())
    return asdict(await TaskService(SqlTaskRepository(session)).create(actor, task))


@router.get("/tasks/{task_id}", response_model=TaskDetailOutput)
async def task_detail(task_id: int, session: Session, actor: CurrentActor) -> dict[str, object]:
    return asdict(await TaskService(SqlTaskRepository(session)).detail(actor, task_id))


@router.patch("/tasks/{task_id}", response_model=TaskOutput)
async def update_task(
    task_id: int, data: TaskPatch, session: Session, actor: CurrentActor
) -> dict[str, object]:
    return asdict(
        await TaskService(SqlTaskRepository(session)).update(
            actor, task_id, TaskChanges(**data.model_dump(exclude_unset=True))
        )
    )


@router.post("/tasks/{task_id}/comments", response_model=CommentOutput, status_code=201)
async def add_comment(
    task_id: int, data: CommentInput, session: Session, actor: CurrentActor
) -> dict[str, object]:
    return asdict(
        await TaskService(SqlTaskRepository(session)).add_comment(actor, task_id, data.text)
    )


@router.post("/tasks/{task_id}/checklist", response_model=ChecklistOutput, status_code=201)
async def add_checklist_item(
    task_id: int, data: WeekInput, session: Session, actor: CurrentActor
) -> dict[str, object]:
    return asdict(
        await TaskService(SqlTaskRepository(session)).add_checklist_item(actor, task_id, data.title)
    )


@router.patch("/tasks/{task_id}/checklist/{item_id}", response_model=ChecklistOutput)
async def toggle_task_checklist(
    task_id: int, item_id: int, data: DoneInput, session: Session, actor: CurrentActor
) -> dict[str, object]:
    return asdict(
        await TaskService(SqlTaskRepository(session)).toggle_checklist_item(
            actor, task_id, item_id, data.done
        )
    )


def week_service(session: Session, actor: CurrentActor) -> WeekService:
    service = WeekService(SqlWeekRepository(session), datetime.now(SARATOV_TIMEZONE).date())
    try:
        service.require_office(actor)
    except PermissionError as error:
        raise HTTPException(403, str(error)) from error
    return service


CurrentWeek = Annotated[WeekService, Depends(week_service)]


@router.get("/week")
async def get_week(
    session: Session,
    service: CurrentWeek,
    actor: CurrentActor,
    week: Annotated[date | None, Query()] = None,
) -> dict[str, object]:
    selected = week or service.week
    if week_start(selected) != selected or selected > service.week:
        raise HTTPException(422, "Выберите среду текущей или прошедшей недели")
    return asdict(await WeekService(SqlWeekRepository(session), selected).get(actor))


@router.post("/week/open")
async def open_week(service: CurrentWeek, actor: CurrentActor) -> dict[str, object]:
    return asdict(await service.open(actor))


@router.post("/week/close")
async def close_week(service: CurrentWeek, actor: CurrentActor) -> dict[str, object]:
    return asdict(await service.close(actor))


@router.post("/week/reopen")
async def reopen_week(service: CurrentWeek, actor: CurrentActor) -> dict[str, object]:
    return asdict(await service.reopen(actor))


@router.get("/planning/weeks")
async def planning_weeks(
    session: Session,
    actor: CurrentActor,
    week: Annotated[date | None, Query()] = None,
) -> list[dict[str, object]]:
    current = week_start(datetime.now(SARATOV_TIMEZONE).date())
    selected = week or current
    if week_start(selected) != selected or selected > current:
        raise HTTPException(422, "Выберите среду текущей или прошедшей недели")
    service = WeekService(SqlWeekRepository(session), selected)
    return [asdict(item) for item in await service.overview(actor)]


@router.post("/week/items", response_model=WeekOutput, status_code=201)
async def add_week_item(data: WeekItemInput, service: CurrentWeek, actor: CurrentActor) -> WeekItem:
    return await service.add(actor, data.title, data.task_id, data.priority_id, data.section)


@router.patch("/week/items/{item_id}", response_model=WeekOutput)
async def toggle_week_item(
    item_id: int, data: DoneInput, service: CurrentWeek, actor: CurrentActor
) -> WeekItem:
    try:
        return await service.toggle(actor, item_id, data.done)
    except LookupError as error:
        raise HTTPException(404, str(error)) from error


@router.put("/week/review")
async def save_review(
    data: ReviewInput, service: CurrentWeek, actor: CurrentActor
) -> dict[str, str]:
    await service.save_review(actor, data.text)
    return {"text": data.text}
