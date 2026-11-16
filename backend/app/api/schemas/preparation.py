from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PreparationInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    ministry_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=240)
    kind: Literal["МСЛ", "КСЛ", "ФКС", "ОМС"]


class PreparationUpdate(BaseModel):
    completed: list[int] = Field(max_length=6)
