from pydantic import BaseModel, ConfigDict, Field


class GoalInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=240)
    year: int = Field(ge=2020, le=2100)
    department_id: int | None = None
    progress: int = Field(default=0, ge=0, le=100)


class PriorityInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=240)
    month: str = Field(pattern=r"^20\d{2}-(0[1-9]|1[0-2])$")
    department_id: int = Field(gt=0)
    goal_id: int | None = None
    progress: int = Field(default=0, ge=0, le=100)


class TemplateInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=120)
    sections: list[str] = Field(min_length=1, max_length=20)
    review_fields: list[str] = Field(min_length=1, max_length=20)
    approved: bool = False
