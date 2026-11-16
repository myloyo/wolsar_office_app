import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.notifications import NotificationRow
from app.infrastructure.models.workspace import UserRow


async def notify(
    session: AsyncSession, user_id: int, title: str, href: str, key: str | None = None
) -> None:
    user = await session.get(UserRow, user_id)
    if user is None or not user.active:
        return
    key = key or uuid.uuid4().hex
    if await session.scalar(select(NotificationRow.id).where(NotificationRow.dedupe_key == key)):
        return
    session.add(
        NotificationRow(
            user_id=user_id,
            title=title[:240],
            href=href,
            created_at=datetime.now(UTC),
            read=False,
            dedupe_key=key,
            push_state="pending",
            attempts=0,
        )
    )
