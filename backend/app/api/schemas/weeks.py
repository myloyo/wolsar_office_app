from pydantic import BaseModel, ConfigDict, Field


class WeekInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=240, pattern=r"\S")


class DoneInput(BaseModel):
    done: bool


class WeekItemInput(WeekInput):
    task_id: int | None = None
    priority_id: int | None = None
    section: str = Field(default="main", min_length=1, max_length=80)


class ReviewInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    text: str = Field(min_length=1, max_length=10000, pattern=r"\S")


class WeekOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    done: bool
    task_id: int | None = None
    priority_id: int | None = None
    section: str = "main"
    carried_from_id: int | None = None
