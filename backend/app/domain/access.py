from app.domain.models import Actor, Role


def require_admin(actor: Actor) -> None:
    if Role.ADMIN not in actor.roles:
        raise PermissionError("Доступно только администратору")


def can_read_space(actor: Actor, scope: str, scope_id: int | None) -> bool:
    if Role.ADMIN in actor.roles:
        return True
    if scope == "common":
        return True
    if scope == "department":
        return scope_id in actor.department_ids
    if scope == "ministry":
        return scope_id in actor.ministry_ids
    return False


def can_write_space(actor: Actor, scope: str, scope_id: int | None) -> bool:
    if Role.ADMIN in actor.roles:
        return True
    if scope == "common":
        return Role.OFFICE in actor.roles
    if scope == "department":
        return Role.OFFICE in actor.roles and scope_id in actor.department_ids
    if scope == "ministry":
        return scope_id in actor.led_ministry_ids
    return False


def can_access_task(
    actor: Actor,
    creator_id: int,
    assignee_id: int,
    department_id: int,
    coexecutor_ids: tuple[int, ...] = (),
    observer_ids: tuple[int, ...] = (),
) -> bool:
    return (
        Role.ADMIN in actor.roles
        or actor.id in {creator_id, assignee_id}
        or actor.id in coexecutor_ids + observer_ids
        or (Role.OFFICE in actor.roles and department_id in actor.department_ids)
    )
