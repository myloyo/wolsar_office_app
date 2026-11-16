from datetime import timedelta
from typing import Literal, Self

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class EventInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=240)
    starts_at: AwareDatetime
    ends_at: AwareDatetime
    kind: Literal["worship", "event", "training"] = "event"
    scope: Literal["common", "department", "ministry"] = "common"
    scope_id: int | None = None
    room_id: int | None = None
    cancelled: bool = False
    expected_version: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def valid_period(self) -> Self:
        if self.ends_at <= self.starts_at or self.ends_at - self.starts_at > timedelta(days=31):
            raise ValueError("Конец события должен быть позже начала; длительность не более 31 дня")
        if (self.scope == "common") != (self.scope_id is None):
            raise ValueError("Для пространства укажите его идентификатор")
        return self


class RoomInput(BaseModel):
    name: str = Field(min_length=1, max_length=120, pattern=r"\S")


class SlotInput(BaseModel):
    event_id: int = Field(gt=0)
    ministry_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=120, pattern=r"\S")
    capacity: int = Field(ge=1, le=100)
