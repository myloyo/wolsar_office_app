from dataclasses import dataclass
from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"
    OFFICE = "office"
    LEADER = "leader"
    VOLUNTEER = "volunteer"


class TaskStatus(StrEnum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    DONE = "done"


@dataclass(frozen=True)
class Actor:
    id: int
    roles: frozenset[Role]
    department_ids: frozenset[int]
    ministry_ids: frozenset[int] = frozenset()
    led_ministry_ids: frozenset[int] = frozenset()
