import hmac
from datetime import UTC, datetime

from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.auth import SESSION_COOKIE
from app.domain.models import Actor, Role
from app.infrastructure.models.auth import SessionRow
from app.infrastructure.models.workspace import MembershipRow, UserRow
from app.infrastructure.settings import settings
from app.utils.auth import digest
from app.utils.dates import aware


async def actor_for(session: AsyncSession, user: UserRow) -> Actor:
    memberships = list(
        await session.scalars(select(MembershipRow).where(MembershipRow.user_id == user.id))
    )
    roles = {Role(r) for r in user.roles}
    if any(m.leader for m in memberships):
        roles.add(Role.LEADER)
    return Actor(
        user.id,
        frozenset(roles),
        frozenset(user.department_ids),
        frozenset(m.ministry_id for m in memberships),
        frozenset(m.ministry_id for m in memberships if m.leader),
    )


async def session_user(request: Request, session: AsyncSession) -> tuple[UserRow, SessionRow]:
    token = request.cookies.get(SESSION_COOKIE, "")
    row = await session.get(SessionRow, digest(token)) if token else None
    if row is None or row.revoked or aware(row.expires_at) <= datetime.now(UTC):
        raise HTTPException(401, "Войдите в приложение")
    user = await session.get(UserRow, row.user_id)
    if user is None or not user.active:
        raise HTTPException(401, "Учётная запись недоступна")
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = request.headers.get("origin")
        if origin and origin != settings.public_origin:
            raise HTTPException(403, "Источник запроса не разрешён")
        csrf = request.headers.get("x-csrf-token", "")
        if not csrf or not hmac.compare_digest(row.csrf_hash, digest(csrf)):
            raise HTTPException(403, "Обновите страницу перед повторным действием")
    return user, row
