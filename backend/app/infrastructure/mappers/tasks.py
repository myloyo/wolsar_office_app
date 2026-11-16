from app.domain.models import TaskStatus
from app.domain.tasks import Task
from app.infrastructure.models.tasks import TaskRow


def to_task(row: TaskRow) -> Task:
    return Task(
        id=row.id,
        title=row.title,
        description=row.description,
        creator_id=row.creator_id,
        assignee_id=row.assignee_id,
        department_id=row.department_id,
        due_date=row.due_date,
        category=row.category,
        priority=row.priority,
        status=TaskStatus(row.status),
        coexecutor_ids=list(row.coexecutor_ids),
        observer_ids=list(row.observer_ids),
        result=row.result,
        version=row.version,
    )
