import secrets
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request, Response
from sqlalchemy import select, update

from app.api.routes import CurrentActor, Session
from app.api.schemas.auth import CodeRequest, CodeVerify
from app.application.auth import AuthService
from app.constants.auth import CSRF_COOKIE, SESSION_COOKIE, SESSION_LIFETIME
from app.infrastructure.auth import SmtpDelivery, SqlAuthStore
from app.infrastructure.models.auth import SessionRow
from app.infrastructure.security import session_user
from app.infrastructure.settings import settings
from app.utils.auth import digest

router = APIRouter(prefix="/api/auth", tags=["Вход"])


def check_origin(request: Request) -> None:
    if request.headers.get("origin") not in {None, settings.public_origin}:
        raise HTTPException(403, "Источник запроса не разрешён")


def set_cookies(response: Response, token: str, csrf: str) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=int(SESSION_LIFETIME.total_seconds()),
        path="/",
    )
    response.set_cookie(
        CSRF_COOKIE,
        csrf,
        httponly=False,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=int(SESSION_LIFETIME.total_seconds()),
        path="/",
    )


@router.post("/request-code")
async def request_code(data: CodeRequest, request: Request, session: Session) -> dict[str, object]:
    check_origin(request)
    service = AuthService(SqlAuthStore(session), SmtpDelivery(), settings.app_secret)
    challenge_id, code = await service.request(
        data.email,
        request.client.host if request.client else "unknown",
        datetime.now(UTC),
        data.purpose,
        data.invitation,
    )
    return {
        "challenge_id": challenge_id,
        "message": "Если адрес допущен, код отправлен на почту",
        "local_code": code
        if settings.local_auth_codes and settings.app_env == "development"
        else None,
    }


@router.post("/verify-code")
async def verify_code(
    data: CodeVerify, request: Request, response: Response, session: Session
) -> dict[str, object]:
    check_origin(request)
    service = AuthService(SqlAuthStore(session), SmtpDelivery(), settings.app_secret)
    result = await service.verify(data.challenge_id, data.code, datetime.now(UTC))
    set_cookies(response, result.token, result.csrf)
    return {"user_id": result.user_id, "csrf_token": result.csrf}


@router.get("/session")
async def current_session(
    request: Request, response: Response, session: Session
) -> dict[str, object]:
    try:
        user, row = await session_user(request, session)
    except HTTPException:
        return {
            "authenticated": False,
            "demo": settings.demo_mode,
            "local_codes": settings.local_auth_codes,
        }
    if not request.cookies.get(CSRF_COOKIE):
        csrf = secrets.token_urlsafe(32)
        row.csrf_hash = digest(csrf)
        await session.commit()
        response.set_cookie(
            CSRF_COOKIE,
            csrf,
            secure=settings.cookie_secure,
            samesite="lax",
            max_age=int(SESSION_LIFETIME.total_seconds()),
            path="/",
        )
    return {
        "authenticated": True,
        "user_id": user.id,
        "name": user.name,
        "demo": False,
        "local_codes": settings.local_auth_codes,
    }


@router.get("/sessions")
async def sessions_list(
    actor: CurrentActor, session: Session, request: Request
) -> list[dict[str, object]]:
    rows = await session.scalars(
        select(SessionRow)
        .where(
            SessionRow.user_id == actor.id,
            SessionRow.revoked.is_(False),
            SessionRow.expires_at > datetime.now(UTC),
        )
        .order_by(SessionRow.created_at.desc())
    )
    current = digest(request.cookies.get(SESSION_COOKIE, ""))
    return [
        {
            "id": r.id,
            "created_at": r.created_at,
            "expires_at": r.expires_at,
            "current": r.id == current,
        }
        for r in rows
    ]


@router.delete("/sessions/{session_id}")
async def revoke_session(session_id: str, actor: CurrentActor, session: Session) -> dict[str, bool]:
    row = await session.get(SessionRow, session_id)
    if row is None or row.user_id != actor.id:
        raise LookupError("Сессия не найдена")
    row.revoked = True
    await session.commit()
    return {"ok": True}


@router.post("/logout")
async def logout(
    request: Request, response: Response, session: Session, actor: CurrentActor
) -> dict[str, bool]:
    row = await session.get(SessionRow, digest(request.cookies.get(SESSION_COOKIE, "")))
    if row and row.user_id == actor.id:
        row.revoked = True
        await session.commit()
    response.delete_cookie(SESSION_COOKIE, path="/")
    response.delete_cookie(CSRF_COOKIE, path="/")
    return {"ok": True}


@router.post("/logout-all")
async def logout_all(response: Response, session: Session, actor: CurrentActor) -> dict[str, bool]:
    await session.execute(
        update(SessionRow).where(SessionRow.user_id == actor.id).values(revoked=True)
    )
    await session.commit()
    response.delete_cookie(SESSION_COOKIE, path="/")
    response.delete_cookie(CSRF_COOKIE, path="/")
    return {"ok": True}
