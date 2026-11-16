import asyncio
import io
import re
import zipfile
from pathlib import Path

from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.types import Record
from app.constants.files import MAX_UPLOAD_BYTES
from app.infrastructure.mappers.files import file_record
from app.infrastructure.models.workspace import FileRow
from app.infrastructure.settings import settings


class LocalBlobs:
    def path(self, file_id: str) -> str:
        if not re.fullmatch(r"[a-f0-9]{32}", file_id):
            raise LookupError("Файл не найден")
        return str(Path(settings.storage_path).resolve() / file_id)

    async def put(self, file_id: str, name: str, body: bytes) -> str:
        def write() -> str:
            if not body or len(body) > MAX_UPLOAD_BYTES:
                raise ValueError("Размер файла должен быть от 1 байта до 10 МБ")
            if len(name) > 240 or any(c in name for c in ("/", "\\", "\r", "\n", "\x00")):
                raise ValueError("Недопустимое имя файла")
            extension = Path(name).suffix.lower()
            media = "application/octet-stream"
            if extension in {".png", ".jpg", ".jpeg", ".webp"}:
                with Image.open(io.BytesIO(body)) as image:
                    if image.width * image.height > 20_000_000 or image.format not in {
                        "PNG",
                        "JPEG",
                        "WEBP",
                    }:
                        raise ValueError("Недопустимое изображение")
                    media = f"image/{image.format.lower()}"
                    image.verify()
            elif extension == ".pdf":
                if not body.startswith(b"%PDF-"):
                    raise ValueError("Содержимое не соответствует PDF")
                media = "application/pdf"
            elif extension in {".txt", ".csv"}:
                body.decode("utf-8-sig")
                media = "text/plain"
            elif extension in {".docx", ".xlsx", ".pptx"}:
                with zipfile.ZipFile(io.BytesIO(body)) as archive:
                    entries = archive.infolist()
                    if len(entries) > 1000 or sum(e.file_size for e in entries) > 50_000_000:
                        raise ValueError("Слишком большой документ")
                    if any(
                        e.file_size > max(e.compress_size, 1) * 200
                        or ".." in Path(e.filename).parts
                        for e in entries
                    ):
                        raise ValueError("Недопустимая структура документа")
                    expected = {".docx": "word/", ".xlsx": "xl/", ".pptx": "ppt/"}[extension]
                    if not any(e.filename.startswith(expected) for e in entries) or any(
                        "vbaproject" in e.filename.lower() for e in entries
                    ):
                        raise ValueError("Формат документа не соответствует расширению")
            else:
                raise ValueError("Разрешены PNG, JPEG, WebP, PDF, TXT, CSV, DOCX, XLSX и PPTX")
            target = Path(self.path(file_id))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(body)
            return media

        try:
            return await asyncio.to_thread(write)
        except (OSError, UnicodeError, zipfile.BadZipFile, Image.DecompressionBombError) as error:
            raise ValueError("Не удалось проверить содержимое файла") from error


class SqlFileStore:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(self, scope: str, scope_id: int) -> list[Record]:
        return [
            file_record(r)
            for r in await self.session.scalars(
                select(FileRow).where(FileRow.scope == scope, FileRow.scope_id == scope_id)
            )
        ]

    async def get(self, file_id: str) -> Record:
        row = await self.session.get(FileRow, file_id)
        if row is None:
            raise LookupError("Файл не найден")
        return file_record(row)

    async def save(self, data: Record) -> Record:
        row = FileRow(**data, deleted=False)
        self.session.add(row)
        await self.session.commit()
        return file_record(row)

    async def deleted(self, file_id: str, deleted: bool) -> None:
        row = await self.session.get(FileRow, file_id)
        if row is None:
            raise LookupError("Файл не найден")
        row.deleted = deleted
        await self.session.commit()
