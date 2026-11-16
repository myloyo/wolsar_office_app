from typing import Protocol

from app.application.types import Record
from app.domain.models import Actor, Role


def require_worship(actor: Actor) -> None:
    if Role.ADMIN not in actor.roles and not (
        Role.OFFICE in actor.roles and 1 in actor.department_ids
    ):
        raise PermissionError("Изменение собрания доступно отделению Богослужения")


class WorshipStore(Protocol):
    async def list_services(self, year: int) -> list[Record]: ...
    async def get(self, event_id: int) -> Record: ...
    async def create(self, actor_id: int, data: Record) -> Record: ...
    async def program(self, event_id: int, data: Record, version: int) -> Record: ...
    async def timer(self, event_id: int, action: str, version: int) -> Record: ...
    async def prayers(self, actor_id: int, all_rows: bool) -> list[Record]: ...
    async def add_prayer(self, actor_id: int, data: Record) -> Record: ...
    async def link_prayer(self, prayer_id: int, event_id: int) -> Record: ...


class WorshipService:
    def __init__(self, store: WorshipStore) -> None:
        self.store = store

    async def list_services(self, actor: Actor, year: int) -> list[Record]:
        return await self.store.list_services(year)

    async def get(self, actor: Actor, event_id: int) -> Record:
        return await self.store.get(event_id)

    async def create(self, actor: Actor, data: Record) -> Record:
        require_worship(actor)
        return await self.store.create(actor.id, data)

    async def program(self, actor: Actor, event_id: int, data: Record, version: int) -> Record:
        require_worship(actor)
        return await self.store.program(event_id, data, version)

    async def timer(self, actor: Actor, event_id: int, action: str, version: int) -> Record:
        require_worship(actor)
        return await self.store.timer(event_id, action, version)

    async def prayers(self, actor: Actor) -> list[Record]:
        allowed = Role.ADMIN in actor.roles or bool({1, 5} & actor.department_ids)
        return await self.store.prayers(actor.id, allowed)

    async def add_prayer(self, actor: Actor, data: Record) -> Record:
        return await self.store.add_prayer(actor.id, data)

    async def link_prayer(self, actor: Actor, prayer_id: int, event_id: int) -> Record:
        require_worship(actor)
        return await self.store.link_prayer(prayer_id, event_id)
