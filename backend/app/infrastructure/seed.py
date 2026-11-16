from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.calendar import SARATOV_TIMEZONE
from app.domain.calendar import week_start
from app.infrastructure.database import sessions
from app.infrastructure.models.planning import TemplateRow, WeekItemRow
from app.infrastructure.models.tasks import TaskRow
from app.infrastructure.models.workspace import DepartmentRow, MembershipRow, MinistryRow, UserRow
from app.infrastructure.seed_constants import DEPARTMENTS


async def seed() -> None:
    async with sessions() as session:
        if await session.scalar(select(UserRow.id).limit(1)):
            await seed_platform(session)
            await session.commit()
            return
        session.add_all(
            [
                DepartmentRow(id=i, name=name, leader="Руководитель не назначен")
                for i, name in enumerate(DEPARTMENTS, 1)
            ]
        )
        session.add_all(
            [
                UserRow(
                    id=1,
                    name="Демо · Исполнительный пастор",
                    roles=["admin", "office"],
                    department_ids=list(range(1, 8)),
                ),
                UserRow(
                    id=2, name="Демо · Сотрудник офиса", roles=["office"], department_ids=[4, 5]
                ),
                UserRow(id=3, name="Демо · Лидер служения", roles=["leader"], department_ids=[]),
                UserRow(id=4, name="Демо · Служитель", roles=["volunteer"], department_ids=[]),
            ]
        )
        await session.flush()
        today = datetime.now(SARATOV_TIMEZONE).date()
        entries = [
            ("Открыть задачи месяца", "personal", "high", 1, 1),
            ("Распечатать приглашения", "leaders", "high", 3, 2),
            ("Подготовить встречу команды", "leaders", "normal", 1, 1),
            ("Запрос на материалы мероприятия", "responsible", "normal", 2, 4),
            ("Инвентаризация оборудования", "responsible", "normal", 1, 1),
            ("Конференция: информация для команды", "information", "normal", 1, 1),
            ("Идея встречи волонтёров", "ideas", "normal", 1, 1),
            ("Приоритеты отделения на месяц", "personal", "normal", 2, 5),
        ]
        session.add_all(
            [
                TaskRow(
                    title=title,
                    description="Демонстрационная задача. Можно редактировать статус.",
                    creator_id=1,
                    assignee_id=assignee,
                    department_id=department,
                    due_date=today + timedelta(days=i - 1),
                    category=category,
                    priority=priority,
                    status="in_progress" if i % 3 == 0 else "new",
                )
                for i, (title, category, priority, assignee, department) in enumerate(entries)
            ]
        )
        session.add_all(
            [
                WeekItemRow(user_id=user_id, week=week_start(today), title=title, done=i == 0)
                for user_id in (1, 2)
                for i, title in enumerate(
                    [
                        "Внести мероприятия ноября в календарь",
                        "Сверить анонсы на неделю",
                        "Подготовить материалы по проекту",
                        "Провести встречу команды",
                    ]
                )
            ]
        )
        await seed_platform(session)
        await session.commit()


async def seed_platform(session: AsyncSession) -> None:
    for user_id, email in [
        (1, "admin@example.test"),
        (2, "office@example.test"),
        (3, "leader@example.test"),
        (4, "volunteer@example.test"),
    ]:
        user = await session.get(UserRow, user_id)
        if user and user.email is None:
            user.email = email
    ministry = await session.scalar(select(MinistryRow).limit(1))
    department = await session.get(DepartmentRow, 1)
    if ministry is None and department is not None:
        ministry = MinistryRow(
            name="Демо · Молодёжное служение",
            department_id=1,
            description="Демонстрационное пространство",
            vision="",
        )
        session.add(ministry)
        await session.flush()
        for user_id in [3, 4]:
            if await session.get(UserRow, user_id):
                session.add(
                    MembershipRow(ministry_id=ministry.id, user_id=user_id, leader=user_id == 3)
                )
    if not await session.scalar(select(TemplateRow.id).limit(1)):
        session.add(
            TemplateRow(
                name="Проект шаблона офиса",
                sections=["Основные задачи", "Проекты", "Развитие"],
                review_fields=["Что получилось", "Что мешало", "Что переносим"],
                approved=False,
            )
        )
