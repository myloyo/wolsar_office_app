from collections.abc import AsyncIterator
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.routes import session_dependency
from app.domain.calendar import week_start
from app.infrastructure.models.base import Base
from app.infrastructure.models.planning import WeekItemRow
from app.infrastructure.models.tasks import TaskRow
from app.infrastructure.models.workspace import DepartmentRow, UserRow
from app.infrastructure.settings import settings
from app.main import app


@pytest_asyncio.fixture
async def client(tmp_path: Path) -> AsyncIterator[AsyncClient]:
    engine = create_async_engine(f"sqlite+aiosqlite:///{(tmp_path / 'test.db').as_posix()}")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with factory() as session:
        session.add(DepartmentRow(id=1, name="Отделение", leader="Не назначен"))
        session.add_all(
            [
                UserRow(
                    id=1,
                    name="Администратор",
                    email="admin@example.test",
                    roles=["admin"],
                    department_ids=[1],
                ),
                UserRow(
                    id=2,
                    name="Служитель",
                    email="volunteer@example.test",
                    roles=["volunteer"],
                    department_ids=[],
                ),
                UserRow(
                    id=3,
                    name="Сотрудник",
                    email="office@example.test",
                    roles=["office"],
                    department_ids=[1],
                ),
            ]
        )
        await session.flush()
        session.add(
            TaskRow(
                id=1,
                title="Закрытая задача",
                description="",
                creator_id=1,
                assignee_id=3,
                department_id=1,
                due_date=date(2026, 11, 4),
                category="personal",
                priority="normal",
                status="new",
            )
        )
        session.add(
            WeekItemRow(
                id=1,
                user_id=1,
                title="Чужой план",
                week=week_start(datetime.now(ZoneInfo("Europe/Saratov")).date()),
                done=False,
            )
        )
        await session.commit()

    async def override():
        async with factory() as session:
            yield session

    previous_codes = settings.local_auth_codes
    settings.local_auth_codes = True
    previous = settings.demo_mode
    settings.demo_mode = True
    app.dependency_overrides[session_dependency] = override
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
            yield http
    finally:
        settings.demo_mode = previous
        settings.local_auth_codes = previous_codes
        app.dependency_overrides.clear()
        await engine.dispose()


@pytest_asyncio.fixture
async def db(client: AsyncClient) -> AsyncIterator[object]:
    async for session in app.dependency_overrides[session_dependency]():
        yield session
