import asyncio
import smtplib
import ssl
from datetime import datetime, timedelta
from email.message import EmailMessage

from sqlalchemy import or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.models.auth import Challenge
from app.constants.auth import MAX_OTP_ATTEMPTS, SESSION_LIFETIME
from app.infrastructure.models.auth import AuthRateRow, ChallengeRow, InvitationRow, SessionRow
from app.infrastructure.models.workspace import UserRow
from app.infrastructure.settings import settings
from app.utils.auth import digest
from app.utils.dates import aware


class SmtpDelivery:
    async def send(self, email: str, code: str) -> None:
        if settings.otp_delivery == "local":
            if not settings.local_auth_codes:
                raise ValueError("Доставка OTP не настроена")
            return

        def send() -> None:
            message = EmailMessage()
            message["Subject"] = "Код входа · СЖ Саратов"
            message["From"] = settings.smtp_from
            message["To"] = email
            message.set_content(f"Код входа: {code}\nДействует 5 минут. Не сообщайте его другим.")
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
                if settings.smtp_tls:
                    smtp.starttls(context=ssl.create_default_context())
                if settings.smtp_user:
                    smtp.login(settings.smtp_user, settings.smtp_password)
                smtp.send_message(message)

        await asyncio.to_thread(send)


class SqlAuthStore:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def rate_allowed(self, email: str, ip_hash: str, now: datetime) -> bool:
        allowed = True
        for namespace, value, window, limit in (
            ("email-minute", email, 60, 1),
            ("email-hour", email, 3600, 6),
            ("ip-hour", ip_hash, 3600, 300),
        ):
            key = digest(f"{namespace}:{value}:{int(now.timestamp()) // window}")
            statement = (
                update(AuthRateRow)
                .where(AuthRateRow.key == key)
                .values(count=AuthRateRow.count + 1)
                .returning(AuthRateRow.count)
            )
            count = await self.session.scalar(statement)
            if count is None:
                try:
                    async with self.session.begin_nested():
                        self.session.add(
                            AuthRateRow(key=key, count=1, expires_at=now + timedelta(hours=2))
                        )
                        await self.session.flush()
                    count = 1
                except IntegrityError:
                    count = await self.session.scalar(statement)
            allowed = allowed and count is not None and count <= limit
        await self.session.commit()
        if not allowed:
            return False
        rows = list(
            await self.session.scalars(
                select(ChallengeRow).where(
                    ChallengeRow.created_at > now - timedelta(hours=1),
                    or_(ChallengeRow.email == email, ChallengeRow.ip_hash == ip_hash),
                )
            )
        )
        own = [r for r in rows if r.email == email]
        return (
            len(own) < 6
            and len(rows) < 300
            and not any(aware(r.created_at) > now - timedelta(seconds=60) for r in own)
        )

    async def eligible(
        self, email: str, invitation: str | None, now: datetime
    ) -> tuple[bool, int | None]:
        user = await self.session.scalar(select(UserRow).where(UserRow.email == email))
        if user and user.active:
            return True, None
        if invitation and user:
            row = await self.session.scalar(
                select(InvitationRow).where(
                    InvitationRow.token_hash == digest(invitation),
                    InvitationRow.email == email,
                    InvitationRow.accepted.is_(False),
                    InvitationRow.expires_at > now,
                )
            )
            if row:
                return True, row.id
        return False, None

    async def create_challenge(self, challenge: Challenge, ip_hash: str, now: datetime) -> None:
        self.session.add(
            ChallengeRow(
                **challenge.__dict__, ip_hash=ip_hash, created_at=now, attempts=0, used=False
            )
        )
        await self.session.commit()

    async def attempt(self, challenge_id: str, now: datetime) -> Challenge | None:
        row = await self.session.scalar(
            update(ChallengeRow)
            .where(
                ChallengeRow.id == challenge_id,
                ChallengeRow.used.is_(False),
                ChallengeRow.attempts < MAX_OTP_ATTEMPTS,
                ChallengeRow.expires_at > now,
            )
            .values(attempts=ChallengeRow.attempts + 1)
            .returning(ChallengeRow)
        )
        await self.session.commit()
        if row is None:
            return None
        return Challenge(
            row.id, row.email, row.code_hash, aware(row.expires_at), row.purpose, row.invitation_id
        )

    async def finish(
        self, challenge: Challenge, token_hash: str, csrf_hash: str, now: datetime
    ) -> int:
        used = await self.session.scalar(
            update(ChallengeRow)
            .where(
                ChallengeRow.id == challenge.id,
                ChallengeRow.used.is_(False),
                ChallengeRow.expires_at > now,
                ChallengeRow.attempts <= 5,
            )
            .values(used=True)
            .returning(ChallengeRow.id)
        )
        user = await self.session.scalar(select(UserRow).where(UserRow.email == challenge.email))
        if not used or user is None:
            await self.session.rollback()
            raise PermissionError("Код недействителен")
        if not user.active:
            accepted = await self.session.scalar(
                update(InvitationRow)
                .where(
                    InvitationRow.id == challenge.invitation_id,
                    InvitationRow.email == challenge.email,
                    InvitationRow.accepted.is_(False),
                    InvitationRow.expires_at > now,
                )
                .values(accepted=True)
                .returning(InvitationRow.id)
            )
            if accepted is None:
                await self.session.rollback()
                raise PermissionError("Учётная запись недоступна")
            user.active = True
        if challenge.purpose == "recovery":
            await self.session.execute(
                update(SessionRow).where(SessionRow.user_id == user.id).values(revoked=True)
            )
        self.session.add(
            SessionRow(
                id=token_hash,
                user_id=user.id,
                csrf_hash=csrf_hash,
                created_at=now,
                expires_at=now + SESSION_LIFETIME,
                revoked=False,
            )
        )
        await self.session.commit()
        return user.id
