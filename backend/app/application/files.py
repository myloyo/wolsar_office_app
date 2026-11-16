from typing import Protocol

from app.application.tasks import TaskService
from app.application.types import Record
from app.application.workspace import WorkspaceStore
from app.domain.access import can_read_space, can_write_space
from app.domain.models import Actor


class FileStore(Protocol):
    async def list(self, scope: str, scope_id: int) -> list[Record]: ...
    async def get(self, file_id: str) -> Record: ...
    async def save(self, data: Record) -> Record: ...
    async def deleted(self, file_id: str, deleted: bool) -> None: ...


class BlobStore(Protocol):
    async def put(self, file_id: str, name: str, body: bytes) -> str: ...
    def path(self, file_id: str) -> str: ...


class FileService:
    def __init__(
        self, store: FileStore, blobs: BlobStore, tasks: TaskService, spaces: WorkspaceStore
    ) -> None:
        self.store, self.blobs, self.tasks, self.spaces = store, blobs, tasks, spaces

    async def authorize(self, actor: Actor, scope: str, scope_id: int, write: bool = False) -> None:
        if scope == "task":
            task = await self.tasks.get_visible(actor, scope_id)
            if write and not task.can_contribute(actor):
                raise PermissionError("Нет прав на вложения задачи")
        else:
            allowed = (
                can_write_space(actor, scope, scope_id)
                if write
                else can_read_space(actor, scope, scope_id)
            )
            if not allowed:
                raise PermissionError("Нет доступа к файлам пространства")
            await self.spaces.space(scope, scope_id)

    async def list(self, actor: Actor, scope: str, scope_id: int) -> list[Record]:
        await self.authorize(actor, scope, scope_id)
        return await self.store.list(scope, scope_id)

    async def upload(
        self, actor: Actor, scope: str, scope_id: int, file_id: str, name: str, body: bytes
    ) -> Record:
        await self.authorize(actor, scope, scope_id, True)
        media = await self.blobs.put(file_id, name, body)
        return await self.store.save(
            {
                "id": file_id,
                "name": name,
                "media_type": media,
                "size": len(body),
                "scope": scope,
                "scope_id": scope_id,
                "uploader_id": actor.id,
            }
        )

    async def download(self, actor: Actor, file_id: str) -> Record:
        row = await self.store.get(file_id)
        await self.authorize(actor, row["scope"], row["scope_id"])
        if row["deleted"]:
            raise LookupError("Файл удалён")
        return {**row, "path": self.blobs.path(file_id)}

    async def delete(self, actor: Actor, file_id: str, deleted: bool) -> None:
        row = await self.store.get(file_id)
        await self.authorize(actor, row["scope"], row["scope_id"], True)
        await self.store.deleted(file_id, deleted)
