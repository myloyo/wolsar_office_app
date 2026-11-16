from dataclasses import dataclass
from datetime import datetime


@dataclass
class Challenge:
    id: str
    email: str
    code_hash: str
    expires_at: datetime
    purpose: str
    invitation_id: int | None


@dataclass
class AuthResult:
    user_id: int
    token: str
    csrf: str
