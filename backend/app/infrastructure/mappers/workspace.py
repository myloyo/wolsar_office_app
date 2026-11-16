from app.application.types import Record
from app.infrastructure.models.workspace import UserRow


def public_user(user: UserRow) -> Record:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "active": user.active,
        "roles": user.roles,
        "department_ids": user.department_ids,
    }
