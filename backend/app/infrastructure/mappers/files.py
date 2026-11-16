from app.application.types import Record
from app.infrastructure.models.workspace import FileRow


def file_record(row: FileRow) -> Record:
    return {
        key: getattr(row, key)
        for key in (
            "id",
            "name",
            "media_type",
            "size",
            "scope",
            "scope_id",
            "uploader_id",
            "deleted",
        )
    }
