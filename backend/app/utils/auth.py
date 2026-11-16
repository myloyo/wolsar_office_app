import hashlib
import hmac
import re


def normalize_email(value: str) -> str:
    value = value.strip().lower()
    if len(value) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
        raise ValueError("Укажите корректную почту")
    return value


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def otp_digest(secret: str, challenge_id: str, code: str) -> str:
    return hmac.new(secret.encode(), f"{challenge_id}:{code}".encode(), hashlib.sha256).hexdigest()
