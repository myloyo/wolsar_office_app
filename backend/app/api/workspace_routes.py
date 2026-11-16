from typing import Literal

from fastapi import APIRouter

from app.api.routes import CurrentActor, Session
from app.api.schemas.workspace import (
    DepartmentInput,
    InviteInput,
    MembershipInput,
    MinistryInput,
    PostInput,
    ProjectInput,
    ProjectStatus,
    RecoverInput,
    UserInput,
)
from app.application.types import Record
from app.application.workspace import WorkspaceService
from app.infrastructure.workspace import SqlWorkspaceStore

router = APIRouter(prefix="/api", tags=["Пространства"])
Scope = Literal["department", "ministry"]


@router.get("/admin/users")
async def users(session: Session, actor: CurrentActor) -> list[Record]:
    return await WorkspaceService(SqlWorkspaceStore(session)).list_users(actor)


@router.put("/admin/users/{user_id}")
async def save_user(user_id: int, data: UserInput, session: Session, actor: CurrentActor) -> Record:
    return await WorkspaceService(SqlWorkspaceStore(session)).save_user(
        actor, user_id, data.model_dump()
    )


@router.post("/admin/invitations", status_code=201)
async def invite(data: InviteInput, session: Session, actor: CurrentActor) -> Record:
    return await WorkspaceService(SqlWorkspaceStore(session)).invite(actor, data.model_dump())


@router.get("/spaces/{scope}")
async def spaces(scope: Scope, session: Session, actor: CurrentActor) -> list[Record]:
    return await WorkspaceService(SqlWorkspaceStore(session)).list_spaces(actor, scope)


@router.get("/spaces/{scope}/{space_id}")
async def space(scope: Scope, space_id: int, session: Session, actor: CurrentActor) -> Record:
    return await WorkspaceService(SqlWorkspaceStore(session)).get_space(actor, scope, space_id)


@router.post("/departments", status_code=201)
async def create_department(data: DepartmentInput, session: Session, actor: CurrentActor) -> Record:
    return await WorkspaceService(SqlWorkspaceStore(session)).save_space(
        actor, "department", None, data.model_dump()
    )


@router.put("/departments/{space_id}")
async def save_department(
    space_id: int, data: DepartmentInput, session: Session, actor: CurrentActor
) -> Record:
    return await WorkspaceService(SqlWorkspaceStore(session)).save_space(
        actor, "department", space_id, data.model_dump()
    )


@router.post("/ministries", status_code=201)
async def create_ministry(data: MinistryInput, session: Session, actor: CurrentActor) -> Record:
    return await WorkspaceService(SqlWorkspaceStore(session)).save_space(
        actor, "ministry", None, data.model_dump()
    )


@router.put("/ministries/{space_id}")
async def save_ministry(
    space_id: int, data: MinistryInput, session: Session, actor: CurrentActor
) -> Record:
    return await WorkspaceService(SqlWorkspaceStore(session)).save_space(
        actor, "ministry", space_id, data.model_dump()
    )


@router.put("/ministries/{space_id}/members")
async def member(
    space_id: int, data: MembershipInput, session: Session, actor: CurrentActor
) -> dict[str, bool]:
    await WorkspaceService(SqlWorkspaceStore(session)).membership(
        actor, space_id, data.user_id, data.leader, False
    )
    return {"ok": True}


@router.delete("/ministries/{space_id}/members/{user_id}")
async def remove_member(
    space_id: int, user_id: int, session: Session, actor: CurrentActor
) -> dict[str, bool]:
    await WorkspaceService(SqlWorkspaceStore(session)).membership(
        actor, space_id, user_id, False, True
    )
    return {"ok": True}


@router.post("/spaces/{scope}/{space_id}/posts", status_code=201)
async def add_post(
    scope: Scope, space_id: int, data: PostInput, session: Session, actor: CurrentActor
) -> Record:
    return await WorkspaceService(SqlWorkspaceStore(session)).add_content(
        actor, "post", scope, space_id, data.model_dump()
    )


@router.post("/spaces/{scope}/{space_id}/projects", status_code=201)
async def add_project(
    scope: Scope, space_id: int, data: ProjectInput, session: Session, actor: CurrentActor
) -> Record:
    return await WorkspaceService(SqlWorkspaceStore(session)).add_content(
        actor, "project", scope, space_id, data.model_dump()
    )


@router.post("/admin/users/{user_id}/recovery")
async def recover_user(
    user_id: int, data: RecoverInput, session: Session, actor: CurrentActor
) -> Record:
    return await WorkspaceService(SqlWorkspaceStore(session)).recover(actor, user_id, data.email)


@router.patch("/projects/{project_id}")
async def project_status(
    project_id: int, data: ProjectStatus, session: Session, actor: CurrentActor
) -> Record:
    return await WorkspaceService(SqlWorkspaceStore(session)).project_status(
        actor, project_id, data.status
    )
