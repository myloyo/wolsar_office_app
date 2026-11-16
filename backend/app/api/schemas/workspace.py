from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models import Role


class DepartmentInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=10000)
    leader: str = Field(default="Не назначен", max_length=120)


class MinistryInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=120)
    department_id: int = Field(gt=0)
    description: str = Field(default="", max_length=10000)
    vision: str = Field(default="", max_length=10000)


class UserInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=120)
    roles: list[Role] = Field(min_length=1, max_length=4)
    department_ids: list[int] = Field(default_factory=list, max_length=100)
    active: bool = True


class InviteInput(UserInput):
    email: str = Field(min_length=3, max_length=254)


class MembershipInput(BaseModel):
    user_id: int = Field(gt=0)
    leader: bool = False


class PostInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    text: str = Field(min_length=1, max_length=10000)


class ProjectInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=240)
    description: str = Field(default="", max_length=10000)


class RecoverInput(BaseModel):
    email: str = Field(min_length=3, max_length=254)


class ProjectStatus(BaseModel):
    status: Literal["active", "done"]
