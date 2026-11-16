from app.application.types import Record
from app.infrastructure.models.calendar import EventRow
from app.utils.dates import aware


def event_record(row: EventRow) -> Record:
    return {
        "id": row.id,
        "title": row.title,
        "starts_at": aware(row.starts_at),
        "ends_at": aware(row.ends_at),
        "kind": row.kind,
        "scope": row.scope,
        "scope_id": row.scope_id,
        "room_id": row.room_id,
        "creator_id": row.creator_id,
        "cancelled": row.cancelled,
        "version": row.version,
    }
