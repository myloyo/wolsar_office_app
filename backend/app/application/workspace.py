from typing import Protocol

from app.application.types import Record
from app.domain.access import can_read_space, can_write_space, require_admin
from app.domain.models import Actor


class WorkspaceStore(Protocol):
    async def spaces(self, kind: str) -> list[Record]: ...
    async def space(self, kind: str, space_id: int) -> Record: ...
    async def save_space(self, kind: str, space_id: int | None, data: Record) -> Record: ...
    async def users(self) -> list[Record]: ...
    async def save_user(self, user_id: int, data: Record, actor_id: int) -> Record: ...
    async def invite(self, data: Record) -> Record: ...
    async def recover(self, user_id: int, email: str) -> Record: ...
    async def project(self, project_id: int) -> Record: ...
    async def project_status(self, project_id: int, status: str) -> Record: ...
    async def membership(
        self, ministry_id: int, user_id: int, leader: bool, remove: bool
    ) -> None: ...
    async def content(self, scope: str, scope_id: int) -> Record: ...
    async def save_content(
        self, kind: str, scope: str, scope_id: int, actor_id: int, data: Record
    ) -> Record: ...


class WorkspaceService:
    def __init__(self, store: WorkspaceStore) -> None:
        self.store = store

    async def list_spaces(self, actor: Actor, kind: str) -> list[Record]:
        return [s for s in await self.store.spaces(kind) if can_read_space(actor, kind, s["id"])]

    async def get_space(self, actor: Actor, kind: str, space_id: int) -> Record:
        if not can_read_space(actor, kind, space_id):
            raise LookupError("Пространство не найдено")
        return {
            **await self.store.space(kind, space_id),
            **await self.store.content(kind, space_id),
        }

    async def save_space(
        self, actor: Actor, kind: str, space_id: int | None, data: Record
    ) -> Record:
        if space_id is None:
            require_admin(actor)
        elif not can_write_space(actor, kind, space_id):
            raise PermissionError("Нет прав на изменение пространства")
        return await self.store.save_space(kind, space_id, data)

    async def list_users(self, actor: Actor) -> list[Record]:
        require_admin(actor)
        return await self.store.users()

    async def save_user(self, actor: Actor, user_id: int, data: Record) -> Record:
        require_admin(actor)
        return await self.store.save_user(user_id, data, actor.id)

    async def invite(self, actor: Actor, data: Record) -> Record:
        require_admin(actor)
        return await self.store.invite(data)

    async def recover(self, actor: Actor, user_id: int, email: str) -> Record:
        require_admin(actor)
        if actor.id == user_id:
            raise PermissionError("Смену почты администратора подтверждает другой администратор")
        return await self.store.recover(user_id, email)

    async def project_status(self, actor: Actor, project_id: int, status: str) -> Record:
        project = await self.store.project(project_id)
        if not can_read_space(actor, project["scope"], project["scope_id"]):
            raise LookupError("Проект не найден")
        if not can_write_space(actor, project["scope"], project["scope_id"]):
            raise PermissionError("Нет прав на изменение проекта")
        return await self.store.project_status(project_id, status)

    async def membership(
        self, actor: Actor, ministry_id: int, user_id: int, leader: bool, remove: bool
    ) -> None:
        require_admin(actor)
        await self.store.membership(ministry_id, user_id, leader, remove)

    async def add_content(
        self, actor: Actor, kind: str, scope: str, scope_id: int, data: Record
    ) -> Record:
        if not can_write_space(actor, scope, scope_id):
            raise PermissionError("Нет прав на публикацию в пространстве")
        return await self.store.save_content(kind, scope, scope_id, actor.id, data)
