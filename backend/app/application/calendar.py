from datetime import datetime
from typing import Protocol

from app.application.types import Record
from app.domain.access import can_read_space, can_write_space
from app.domain.models import Actor


class CalendarStore(Protocol):
    async def list_events(self, start: datetime, end: datetime) -> list[Record]: ...
    async def event(self, event_id: int) -> Record: ...
    async def save(self, event_id: int | None, actor_id: int, data: Record) -> Record: ...
    async def slots(self) -> list[Record]: ...
    async def add_slot(self, data: Record) -> Record: ...
    async def signup(self, slot_id: int, user_id: int, cancel: bool) -> Record: ...


class CalendarService:
    def __init__(self, store: CalendarStore) -> None:
        self.store = store

    async def events(self, actor: Actor, start: datetime, end: datetime) -> list[Record]:
        return [
            e
            for e in await self.store.list_events(start, end)
            if can_read_space(actor, e["scope"], e["scope_id"])
        ]

    async def get(self, actor: Actor, event_id: int) -> Record:
        event = await self.store.event(event_id)
        if not can_read_space(actor, event["scope"], event["scope_id"]):
            raise LookupError("Событие не найдено")
        return event

    async def save(self, actor: Actor, event_id: int | None, data: Record) -> Record:
        if event_id:
            old = await self.get(actor, event_id)
            if not can_write_space(actor, old["scope"], old["scope_id"]):
                raise PermissionError("Нет прав на изменение события")
        if not can_write_space(actor, data["scope"], data["scope_id"]):
            raise PermissionError("Нет прав на календарь пространства")
        return await self.store.save(event_id, actor.id, data)

    async def slots(self, actor: Actor) -> list[Record]:
        return [
            s
            for s in await self.store.slots()
            if can_read_space(actor, "ministry", s["ministry_id"])
        ]

    async def add_slot(self, actor: Actor, data: Record) -> Record:
        if not can_write_space(actor, "ministry", data["ministry_id"]):
            raise PermissionError("Слоты создаёт лидер служения")
        await self.get(actor, data["event_id"])
        return await self.store.add_slot(data)

    async def signup(self, actor: Actor, slot_id: int, cancel: bool) -> Record:
        slot = next((s for s in await self.slots(actor) if s["id"] == slot_id), None)
        if slot is None:
            raise LookupError("Слот не найден")
        await self.get(actor, slot["event_id"])
        return await self.store.signup(slot_id, actor.id, cancel)
