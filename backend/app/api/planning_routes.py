from fastapi import APIRouter

from app.api.routes import CurrentActor, Session
from app.api.schemas.planning import GoalInput, PriorityInput, TemplateInput
from app.application.planning import PlanningService
from app.application.types import Record
from app.infrastructure.planning import SqlPlanningStore

router = APIRouter(prefix="/api/planning", tags=["Планирование"])


@router.get("/goals")
async def goals(year: int, session: Session, actor: CurrentActor) -> list[Record]:
    return await PlanningService(SqlPlanningStore(session)).list(actor, "goal", str(year))


@router.post("/goals", status_code=201)
async def add_goal(data: GoalInput, session: Session, actor: CurrentActor) -> Record:
    return await PlanningService(SqlPlanningStore(session)).save(
        actor, "goal", None, data.model_dump()
    )


@router.put("/goals/{item_id}")
async def save_goal(item_id: int, data: GoalInput, session: Session, actor: CurrentActor) -> Record:
    return await PlanningService(SqlPlanningStore(session)).save(
        actor, "goal", item_id, data.model_dump()
    )


@router.get("/priorities")
async def priorities(month: str, session: Session, actor: CurrentActor) -> list[Record]:
    return await PlanningService(SqlPlanningStore(session)).list(actor, "priority", month)


@router.post("/priorities", status_code=201)
async def add_priority(data: PriorityInput, session: Session, actor: CurrentActor) -> Record:
    return await PlanningService(SqlPlanningStore(session)).save(
        actor, "priority", None, data.model_dump()
    )


@router.put("/priorities/{item_id}")
async def save_priority(
    item_id: int, data: PriorityInput, session: Session, actor: CurrentActor
) -> Record:
    return await PlanningService(SqlPlanningStore(session)).save(
        actor, "priority", item_id, data.model_dump()
    )


@router.get("/templates")
async def templates(session: Session, actor: CurrentActor) -> list[Record]:
    return await PlanningService(SqlPlanningStore(session)).list(actor, "template", "all")


@router.post("/templates", status_code=201)
async def add_template(data: TemplateInput, session: Session, actor: CurrentActor) -> Record:
    return await PlanningService(SqlPlanningStore(session)).save(
        actor, "template", None, data.model_dump()
    )


@router.put("/templates/{item_id}")
async def save_template(
    item_id: int, data: TemplateInput, session: Session, actor: CurrentActor
) -> Record:
    return await PlanningService(SqlPlanningStore(session)).save(
        actor, "template", item_id, data.model_dump()
    )


@router.get("/report")
async def report(month: str, session: Session, actor: CurrentActor) -> Record:
    return await PlanningService(SqlPlanningStore(session)).report(actor, month)
