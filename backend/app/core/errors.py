"""Application-level error types and HTTP exception handlers."""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class ApplicationError(Exception):
    """Base class for expected application-level failures."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 400,
        code: str = "application_error",
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


async def application_error_handler(
    request: Request,
    exc: ApplicationError,
) -> JSONResponse:
    """Return a controlled response for expected application errors."""
    logger.warning(
        "Application error on %s %s: %s",
        request.method,
        request.url.path,
        exc.code,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "code": exc.code,
        },
    )


async def unexpected_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Return a generic response without leaking internal details."""
    logger.exception(
        "Unhandled application error on %s %s",
        request.method,
        request.url.path,
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "code": "internal_server_error",
        },
    )
