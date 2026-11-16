import hmac
import secrets
from datetime import datetime
from typing import Protocol

from app.application.models.auth import AuthResult, Challenge
from app.constants.auth import OTP_LIFETIME
from app.domain.exceptions import RateLimitError
from app.utils.auth import digest, normalize_email, otp_digest


class AuthStore(Protocol):
    async def rate_allowed(self, email: str, ip_hash: str, now: datetime) -> bool: ...
    async def eligible(
        self, email: str, invitation: str | None, now: datetime
    ) -> tuple[bool, int | None]: ...
    async def create_challenge(self, challenge: Challenge, ip_hash: str, now: datetime) -> None: ...
    async def attempt(self, challenge_id: str, now: datetime) -> Challenge | None: ...
    async def finish(
        self, challenge: Challenge, token_hash: str, csrf_hash: str, now: datetime
    ) -> int: ...


class CodeDelivery(Protocol):
    async def send(self, email: str, code: str) -> None: ...


class AuthService:
    def __init__(self, store: AuthStore, delivery: CodeDelivery, secret: str) -> None:
        self.store, self.delivery, self.secret = store, delivery, secret

    async def request(
        self,
        email: str,
        ip: str,
        now: datetime,
        purpose: str = "login",
        invitation: str | None = None,
    ) -> tuple[str, str | None]:
        email = normalize_email(email)
        ip_hash = otp_digest(self.secret, "ip", ip)
        if not await self.store.rate_allowed(email, ip_hash, now):
            raise RateLimitError("Слишком много запросов. Подождите перед повторной отправкой.")
        allowed, invitation_id = await self.store.eligible(email, invitation, now)
        challenge_id = secrets.token_urlsafe(24)
        code = f"{secrets.randbelow(1000000):06d}"
        await self.store.create_challenge(
            Challenge(
                challenge_id,
                email,
                otp_digest(self.secret, challenge_id, code),
                now + OTP_LIFETIME,
                purpose,
                invitation_id,
            ),
            ip_hash,
            now,
        )
        if allowed:
            await self.delivery.send(email, code)
        return challenge_id, code if allowed else None

    async def verify(self, challenge_id: str, code: str, now: datetime) -> AuthResult:
        challenge = await self.store.attempt(challenge_id, now)
        if challenge is None or not hmac.compare_digest(
            challenge.code_hash, otp_digest(self.secret, challenge_id, code)
        ):
            raise PermissionError("Код недействителен, истёк или исчерпаны попытки")
        token, csrf = secrets.token_urlsafe(48), secrets.token_urlsafe(32)
        user_id = await self.store.finish(challenge, digest(token), digest(csrf), now)
        return AuthResult(user_id, token, csrf)
