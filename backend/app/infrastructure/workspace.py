import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.types import Record
from app.domain.exceptions import ConflictError
from app.infrastructure.mappers.workspace import public_user
from app.infrastructure.models.auth import InvitationRow, SessionRow
from app.infrastructure.models.calendar import EventRow, SignupRow, SlotRow
from app.infrastructure.models.workspace import (
    DepartmentRow,
    MembershipRow,
    MinistryRow,
    PostRow,
    ProjectRow,
    UserRow,
)
from app.utils.auth import digest, normalize_email


class SqlWorkspaceStore:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def spaces(self, kind: str) -> list[Record]:
        if kind == "department":
            return [
                {"id": r.id, "name": r.name, "description": r.description, "leader": r.leader}
                for r in await self.session.scalars(
                    select(DepartmentRow).order_by(DepartmentRow.id)
                )
            ]
        return [
            {
                "id": r.id,
                "name": r.name,
                "description": r.description,
                "vision": r.vision,
                "department_id": r.department_id,
            }
            for r in await self.session.scalars(select(MinistryRow).order_by(MinistryRow.id))
        ]

    async def space(self, kind: str, space_id: int) -> Record:
        row = next((r for r in await self.spaces(kind) if r["id"] == space_id), None)
        if row is None:
            raise LookupError("Пространство не найдено")
        return row

    async def save_space(self, kind: str, space_id: int | None, data: Record) -> Record:
        row: DepartmentRow | MinistryRow | None
        if kind == "department":
            row = await self.session.get(DepartmentRow, space_id) if space_id else DepartmentRow()
        else:
            if await self.session.get(DepartmentRow, data["department_id"]) is None:
                raise ValueError("Отделение не найдено")
            row = await self.session.get(MinistryRow, space_id) if space_id else MinistryRow()
        if row is None:
            raise LookupError("Пространство не найдено")
        for key, value in data.items():
            setattr(row, key, value)
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return await self.space(kind, row.id)

    async def users(self) -> list[Record]:
        return [
            public_user(u) for u in await self.session.scalars(select(UserRow).order_by(UserRow.id))
        ]

    async def validate_departments_exist(self, ids: list[int]) -> None:
        found = set(
            await self.session.scalars(select(DepartmentRow.id).where(DepartmentRow.id.in_(ids)))
        )
        if found != set(ids):
            raise ValueError("Одно из отделений не найдено")

    async def save_user(self, user_id: int, data: Record, actor_id: int) -> Record:
        users = list(
            await self.session.scalars(select(UserRow).order_by(UserRow.id).with_for_update())
        )
        caller = next((u for u in users if u.id == actor_id), None)
        if caller is None or not caller.active or "admin" not in caller.roles:
            raise PermissionError("Права администратора изменились")
        user = next((u for u in users if u.id == user_id), None)
        if user is None:
            raise LookupError("Пользователь не найден")
        if user_id == actor_id and (not data["active"] or "admin" not in data["roles"]):
            raise ConflictError("Нельзя отключить себя или снять собственную роль администратора")
        if "admin" in user.roles and (not data["active"] or "admin" not in data["roles"]):
            if sum(u.active and "admin" in u.roles for u in users) <= 1:
                raise ConflictError("Нельзя отключить последнего администратора")
        await self.validate_departments_exist(data["department_ids"])
        for key, value in data.items():
            setattr(user, key, value)
        await self.session.execute(
            update(SessionRow).where(SessionRow.user_id == user_id).values(revoked=True)
        )
        if not user.active:
            await self.release_slots(user_id)
        await self.session.commit()
        return public_user(user)

    async def invite(self, data: Record) -> Record:
        email = normalize_email(data["email"])
        await self.validate_departments_exist(data["department_ids"])
        user = await self.session.scalar(select(UserRow).where(UserRow.email == email))
        if user and user.active:
            raise ConflictError("Пользователь уже активен")
        if user is None:
            user = UserRow(
                email=email,
                name=data["name"],
                roles=data["roles"],
                department_ids=data["department_ids"],
                active=False,
            )
            self.session.add(user)
            await self.session.flush()
        else:
            user.name, user.roles, user.department_ids = (
                data["name"],
                data["roles"],
                data["department_ids"],
            )
            await self.session.execute(
                update(InvitationRow).where(InvitationRow.user_id == user.id).values(accepted=True)
            )
        token = secrets.token_urlsafe(32)
        row = InvitationRow(
            email=email,
            user_id=user.id,
            token_hash=digest(token),
            expires_at=datetime.now(UTC) + timedelta(days=3),
            accepted=False,
        )
        self.session.add(row)
        await self.session.commit()
        return {"user": public_user(user), "invitation": token, "expires_at": row.expires_at}

    async def membership(self, ministry_id: int, user_id: int, leader: bool, remove: bool) -> None:
        if (
            await self.session.get(MinistryRow, ministry_id) is None
            or await self.session.get(UserRow, user_id) is None
        ):
            raise LookupError("Служение или пользователь не найдены")
        row = await self.session.get(MembershipRow, (ministry_id, user_id))
        if remove:
            if row:
                await self.session.delete(row)
            await self.release_slots(user_id, ministry_id)
        elif row:
            row.leader = leader
        else:
            self.session.add(MembershipRow(ministry_id=ministry_id, user_id=user_id, leader=leader))
        await self.session.commit()

    async def content(self, scope: str, scope_id: int) -> Record:
        users = list(await self.session.scalars(select(UserRow).where(UserRow.active.is_(True))))
        memberships = (
            list(
                await self.session.scalars(
                    select(MembershipRow).where(MembershipRow.ministry_id == scope_id)
                )
            )
            if scope == "ministry"
            else []
        )
        members = [
            {
                "id": u.id,
                "name": u.name,
                "leader": any(m.user_id == u.id and m.leader for m in memberships),
            }
            for u in users
            if (
                scope_id in u.department_ids
                if scope == "department"
                else any(m.user_id == u.id for m in memberships)
            )
        ]
        posts = await self.session.scalars(
            select(PostRow)
            .where(PostRow.scope == scope, PostRow.scope_id == scope_id)
            .order_by(PostRow.created_at.desc())
        )
        projects = await self.session.scalars(
            select(ProjectRow).where(ProjectRow.scope == scope, ProjectRow.scope_id == scope_id)
        )
        return {
            "members": members,
            "posts": [
                {"id": p.id, "author_id": p.author_id, "text": p.text, "created_at": p.created_at}
                for p in posts
            ],
            "projects": [
                {
                    "id": p.id,
                    "title": p.title,
                    "description": p.description,
                    "owner_id": p.owner_id,
                    "status": p.status,
                }
                for p in projects
            ],
        }

    async def save_content(
        self, kind: str, scope: str, scope_id: int, actor_id: int, data: Record
    ) -> Record:
        await self.space(scope, scope_id)
        row: PostRow | ProjectRow
        if kind == "post":
            row = PostRow(
                scope=scope,
                scope_id=scope_id,
                author_id=actor_id,
                text=data["text"],
                created_at=datetime.now(UTC),
            )
        else:
            row = ProjectRow(
                scope=scope,
                scope_id=scope_id,
                owner_id=actor_id,
                title=data["title"],
                description=data["description"],
                status="active",
            )
        self.session.add(row)
        await self.session.commit()
        return await self.content(scope, scope_id)

    async def recover(self, user_id: int, email: str) -> Record:
        user = await self.session.get(UserRow, user_id)
        if user is None:
            raise LookupError("Пользователь не найден")
        user.email, user.active = normalize_email(email), False
        await self.session.execute(
            update(SessionRow).where(SessionRow.user_id == user_id).values(revoked=True)
        )
        await self.session.execute(
            update(InvitationRow).where(InvitationRow.user_id == user_id).values(accepted=True)
        )
        token = secrets.token_urlsafe(32)
        invitation = InvitationRow(
            user_id=user_id,
            email=user.email,
            token_hash=digest(token),
            expires_at=datetime.now(UTC) + timedelta(days=3),
            accepted=False,
        )
        self.session.add(invitation)
        await self.session.commit()
        return {"invitation": token, "user_id": user_id, "expires_at": invitation.expires_at}

    async def project(self, project_id: int) -> Record:
        row = await self.session.get(ProjectRow, project_id)
        if row is None:
            raise LookupError("Проект не найден")
        return {
            "id": row.id,
            "scope": row.scope,
            "scope_id": row.scope_id,
            "title": row.title,
            "description": row.description,
            "status": row.status,
        }

    async def project_status(self, project_id: int, status: str) -> Record:
        row = await self.session.get(ProjectRow, project_id)
        if row is None:
            raise LookupError("Проект не найден")
        row.status = status
        await self.session.commit()
        return await self.project(project_id)

    async def release_slots(self, user_id: int, ministry_id: int | None = None) -> None:
        query = (
            select(SlotRow)
            .join(EventRow, SlotRow.event_id == EventRow.id)
            .join(SignupRow, SignupRow.slot_id == SlotRow.id)
            .where(
                SignupRow.user_id == user_id,
                SignupRow.status == "active",
                EventRow.ends_at > datetime.now(UTC),
            )
        )
        if ministry_id is not None:
            query = query.where(SlotRow.ministry_id == ministry_id)
        slots = list(await self.session.scalars(query))
        from app.infrastructure.notifications import notify

        for slot in slots:
            signup = await self.session.get(SignupRow, (slot.id, user_id))
            if signup:
                signup.status = "replacement"
            leaders = await self.session.scalars(
                select(MembershipRow).where(
                    MembershipRow.ministry_id == slot.ministry_id, MembershipRow.leader.is_(True)
                )
            )
            for leader in leaders:
                await notify(self.session, leader.user_id, "Нужна замена в служении", "/slots")
