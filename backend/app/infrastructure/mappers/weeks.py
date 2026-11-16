from app.application.models.weeks import WeekItem
from app.infrastructure.models.planning import WeekItemRow


def to_item(row: WeekItemRow) -> WeekItem:
    return WeekItem(
        row.id, row.title, row.done, row.task_id, row.priority_id, row.section, row.carried_from_id
    )
