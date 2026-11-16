from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.auth_routes import router as auth_router
from app.api.calendar_routes import router as calendar_router
from app.api.exceptions import install_error_handlers
from app.api.file_routes import router as file_router
from app.api.notification_routes import router as notification_router
from app.api.people_routes import router as people_router
from app.api.planning_routes import router as planning_router
from app.api.preparation_routes import router as preparation_router
from app.api.recurrence_routes import router as recurrence_router
from app.api.routes import router
from app.api.task_extra_routes import router as task_extra_router
from app.api.workspace_routes import router as workspace_router
from app.api.worship_routes import router as worship_router
from app.infrastructure.database import engine
from app.infrastructure.seed import seed
from app.infrastructure.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if settings.demo_mode:
        await seed()
    yield
    await engine.dispose()


app = FastAPI(title="СЖ Саратов", version="0.1.0", lifespan=lifespan)
app.include_router(router)
for module_router in (
    auth_router,
    workspace_router,
    calendar_router,
    worship_router,
    file_router,
    task_extra_router,
    planning_router,
    notification_router,
    recurrence_router,
    preparation_router,
    people_router,
):
    app.include_router(module_router)
install_error_handlers(app)
