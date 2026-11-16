import asyncio
import logging
from datetime import UTC, datetime

from app.infrastructure.database import sessions
from app.infrastructure.jobs import deliver_push, run_jobs


async def main() -> None:
    while True:
        try:
            async with sessions() as session:
                await run_jobs(session, datetime.now(UTC))
                await deliver_push(session)
        except Exception:
            logging.exception("Background jobs failed; retrying in one minute")
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
