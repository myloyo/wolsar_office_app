from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CodeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    email: str = Field(min_length=3, max_length=254)
    purpose: Literal["login", "recovery"] = "login"
    invitation: str | None = Field(default=None, max_length=100)


class CodeVerify(BaseModel):
    challenge_id: str = Field(min_length=20, max_length=64)
    code: str = Field(pattern=r"^\d{6}$")
