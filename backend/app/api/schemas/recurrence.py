from datetime import date
from typing import Literal

from pydantic import BaseModel


class RecurrenceInput(BaseModel):
    frequency: Literal["weekly", "monthly"]
    next_date: date
    active: bool = True
