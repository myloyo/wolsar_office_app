from typing import Protocol

from app.application.types import Record
from app.domain.access import can_read_space, can_write_space, require_admin
from app.domain.models import Actor


class PlanningStore(Protocol):
    async def list(self, kind: str, period: str) -> list[Record]: ...
    async def save(self, kind: str, item_id: int | None, data: Record) -> Record: ...
    async def report(self, month: str) -> Record: ...


class PlanningService:
    def __init__(self, store: PlanningStore) -> None:
        self.store = store

    async def list(self, actor: Actor, kind: str, period: str) -> list[Record]:
        rows = await self.store.list(kind, period)
        return (
            rows
            if kind == "template"
            else [
                r
                for r in rows
                if r.get("department_id") is None
                or can_read_space(actor, "department", r["department_id"])
            ]
        )

    async def save(self, actor: Actor, kind: str, item_id: int | None, data: Record) -> Record:
        if kind in {"goal", "template"}:
            require_admin(actor)
        elif not can_write_space(actor, "department", data["department_id"]):
            raise PermissionError("Нет доступа к приоритетам отделения")
        if item_id and kind == "priority":
            old = next((r for r in await self.store.list(kind, "all") if r["id"] == item_id), None)
            if old is None or not can_write_space(actor, "department", old["department_id"]):
                raise LookupError("Приоритет не найден")
        return await self.store.save(kind, item_id, data)

    async def report(self, actor: Actor, month: str) -> Record:
        require_admin(actor)
        return await self.store.report(month)
