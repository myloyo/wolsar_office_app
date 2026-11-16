import argparse
import asyncio

from sqlalchemy import select

from app.infrastructure.database import sessions
from app.infrastructure.models.workspace import UserRow
from app.utils.auth import normalize_email


async def create_admin(email: str, name: str) -> None:
    async with sessions() as session:
        if await session.scalar(select(UserRow.id).where(UserRow.email == normalize_email(email))):
            raise ValueError("Адрес уже зарегистрирован; роли меняются через администратора")
        if not name.strip():
            raise ValueError("Укажите имя")
        session.add(
            UserRow(
                name=name.strip(),
                email=normalize_email(email),
                roles=["admin", "office"],
                department_ids=[],
                active=True,
            )
        )
        await session.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("email")
    parser.add_argument("name")
    args = parser.parse_args()
    asyncio.run(create_admin(args.email, args.name))
