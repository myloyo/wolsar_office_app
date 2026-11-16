import uuid
from typing import Literal

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse

from app.api.routes import CurrentActor, Session
from app.application.files import FileService
from app.application.tasks import TaskService
from app.application.types import Record
from app.constants.files import MAX_UPLOAD_BYTES
from app.infrastructure.files import LocalBlobs, SqlFileStore
from app.infrastructure.tasks import SqlTaskRepository
from app.infrastructure.workspace import SqlWorkspaceStore

router = APIRouter(prefix="/api", tags=["Файлы"])


def service(session: Session) -> FileService:
    return FileService(
        SqlFileStore(session),
        LocalBlobs(),
        TaskService(SqlTaskRepository(session)),
        SqlWorkspaceStore(session),
    )


@router.get("/files")
async def files(
    scope: Literal["task", "department", "ministry"],
    scope_id: int,
    session: Session,
    actor: CurrentActor,
) -> list[Record]:
    return await service(session).list(actor, scope, scope_id)


@router.post("/files", status_code=201)
async def upload(
    scope: Literal["task", "department", "ministry"],
    scope_id: int,
    name: str,
    request: Request,
    session: Session,
    actor: CurrentActor,
) -> Record:
    await service(session).authorize(actor, scope, scope_id, True)
    chunks, size = [], 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > MAX_UPLOAD_BYTES:
            raise ValueError("Файл превышает 10 МБ")
        chunks.append(chunk)
    return await service(session).upload(
        actor, scope, scope_id, uuid.uuid4().hex, name, b"".join(chunks)
    )


@router.get("/files/{file_id}/download")
async def download(file_id: str, session: Session, actor: CurrentActor) -> FileResponse:
    row = await service(session).download(actor, file_id)
    return FileResponse(
        row["path"],
        filename=row["name"],
        media_type="application/octet-stream",
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
    )


@router.delete("/files/{file_id}")
async def delete_file(file_id: str, session: Session, actor: CurrentActor) -> dict[str, bool]:
    await service(session).delete(actor, file_id, True)
    return {"ok": True}


@router.post("/files/{file_id}/restore")
async def restore_file(file_id: str, session: Session, actor: CurrentActor) -> dict[str, bool]:
    await service(session).delete(actor, file_id, False)
    return {"ok": True}
