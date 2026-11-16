from typing import Any

from fastapi import APIRouter
from sqlalchemy import select

from app.api.routes import CurrentActor, Session
from app.api.schemas.notification import PushInput
from app.infrastructure.models.notifications import NotificationRow, SubscriptionRow
from app.infrastructure.settings import settings
from app.utils.auth import digest

router = APIRouter(prefix="/api/notifications", tags=["Уведомления"])


@router.get("")
async def notifications(session: Session, actor: CurrentActor) -> list[dict[str, Any]]:
    rows = await session.scalars(
        select(NotificationRow)
        .where(NotificationRow.user_id == actor.id)
        .order_by(NotificationRow.created_at.desc())
        .limit(100)
    )
    return [
        {"id": r.id, "title": r.title, "href": r.href, "created_at": r.created_at, "read": r.read}
        for r in rows
    ]


@router.post("/{item_id}/read")
async def read(item_id: int, session: Session, actor: CurrentActor) -> dict[str, bool]:
    row = await session.get(NotificationRow, item_id)
    if row is None or row.user_id != actor.id:
        raise LookupError("Уведомление не найдено")
    row.read = True
    await session.commit()
    return {"ok": True}


@router.get("/push/key")
async def push_key(actor: CurrentActor) -> dict[str, str]:
    return {"key": settings.push_public_key}


@router.post("/push/subscribe")
async def subscribe(data: PushInput, session: Session, actor: CurrentActor) -> dict[str, bool]:
    hashed = digest(data.endpoint)
    row = await session.scalar(
        select(SubscriptionRow).where(SubscriptionRow.endpoint_hash == hashed)
    )
    if row and row.user_id != actor.id:
        raise PermissionError("Подписка принадлежит другому пользователю")
    if row:
        row.keys = data.keys
    else:
        session.add(
            SubscriptionRow(
                user_id=actor.id, endpoint=data.endpoint, endpoint_hash=hashed, keys=data.keys
            )
        )
    await session.commit()
    return {"ok": True}


@router.post("/push/unsubscribe")
async def unsubscribe(data: PushInput, session: Session, actor: CurrentActor) -> dict[str, bool]:
    row = await session.scalar(
        select(SubscriptionRow).where(
            SubscriptionRow.user_id == actor.id,
            SubscriptionRow.endpoint_hash == digest(data.endpoint),
        )
    )
    if row:
        await session.delete(row)
        await session.commit()
    return {"ok": True}
