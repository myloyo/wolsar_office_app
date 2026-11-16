from datetime import date
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ServiceInput(BaseModel):
    day: date
    kind: Literal["1 ВС", "2 ВС", "ОП", "ВХМ"]


class BlockInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    id: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=240)
    minutes: int = Field(ge=1, le=180)
    owner_id: int | None = None
    note: str = Field(default="", max_length=2000)


class McInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    host_id: int | None = None
    value: Literal["Служение", "Спасение", "Духовный рост", "Слово"] = "Служение"
    text: str = Field(default="", max_length=10000)
    story: str = Field(default="", max_length=10000)
    slides: str = Field(default="", max_length=10000)
    ready: bool = False


class ProgramInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    blocks: list[BlockInput] = Field(min_length=1, max_length=100)
    assignments: dict[str, int | None] = Field(max_length=50)
    mc: McInput
    expected_version: int = Field(ge=1)

    @model_validator(mode="after")
    def unique_blocks(self) -> Self:
        if (
            len({b.id for b in self.blocks}) != len(self.blocks)
            or sum(b.minutes for b in self.blocks) > 720
        ):
            raise ValueError("Блоки должны иметь уникальные ID; программа не более 12 часов")
        return self


class TimerAction(BaseModel):
    action: Literal["start", "pause", "next", "previous", "minute", "reset"]
    expected_version: int = Field(ge=1)


class PrayerInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=240)
    details: str = Field(default="", max_length=10000)


class PrayerLink(BaseModel):
    event_id: int = Field(gt=0)
