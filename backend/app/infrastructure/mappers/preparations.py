from app.application.types import Record
from app.infrastructure.models.calendar import PreparationRow


def preparation_record(row: PreparationRow) -> Record:
    return {
        "id": row.id,
        "ministry_id": row.ministry_id,
        "title": row.title,
        "kind": row.kind,
        "steps": row.steps,
        "completed": row.completed,
    }
