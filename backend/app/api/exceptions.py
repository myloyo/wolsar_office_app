from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.domain.exceptions import ConflictError, RateLimitError


def install_error_handlers(app: FastAPI) -> None:
    async def handler(request: Request, error: Exception) -> JSONResponse:
        if isinstance(error, RateLimitError):
            status = 429
        elif isinstance(error, (ConflictError, IntegrityError)):
            status = 409
        elif isinstance(error, PermissionError):
            status = 403
        elif isinstance(error, LookupError):
            status = 404
        else:
            status = 422
        detail = (
            "Запись уже существует или связана с другими данными"
            if isinstance(error, IntegrityError)
            else str(error)
        )
        return JSONResponse(status_code=status, content={"detail": detail})

    for error_type in (
        ConflictError,
        RateLimitError,
        IntegrityError,
        PermissionError,
        LookupError,
        ValueError,
    ):
        app.add_exception_handler(error_type, handler)
