import secrets
from typing import Literal, Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./office.db"
    demo_mode: bool = False
    app_env: Literal["development", "production"] = "development"
    app_secret: str = Field(default_factory=lambda: secrets.token_urlsafe(48))
    public_origin: str = "http://127.0.0.1:5173"
    cookie_secure: bool = False
    local_auth_codes: bool = False
    otp_delivery: Literal["local", "smtp"] = "local"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_tls: bool = True
    storage_path: str = "./uploads"
    push_private_key: str = ""
    push_public_key: str = ""
    push_contact: str = ""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def secure_production(self) -> Self:
        if self.app_env == "production":
            if self.demo_mode or self.local_auth_codes or self.otp_delivery != "smtp":
                raise ValueError("Production requires SMTP and disables demo/local codes")
            if not self.cookie_secure or not self.public_origin.startswith("https://"):
                raise ValueError("Production requires HTTPS and secure cookies")
            if "app_secret" not in self.model_fields_set or len(self.app_secret) < 32:
                raise ValueError("Set APP_SECRET with at least 32 random characters")
            if self.app_secret.startswith("local-development-only"):
                raise ValueError("Replace the development APP_SECRET before production")
            if not self.smtp_host or not self.smtp_from:
                raise ValueError("Set SMTP_HOST and SMTP_FROM")
        return self


settings = Settings()
