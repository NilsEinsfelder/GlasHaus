"""Main application module for the GlasHaus backend."""

from fastapi import FastAPI, Request
from starlette.responses import Response

from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.errors import (
    ApplicationError,
    application_error_handler,
    unexpected_error_handler,
)
from app.core.logging import configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the GlasHaus FastAPI application."""
    resolved_settings = settings or get_settings()

    configure_logging(resolved_settings.log_level)

    application = FastAPI(
        title=resolved_settings.app_name,
    )

    application.add_exception_handler(
        ApplicationError,
        _application_error_handler,
    )
    application.add_exception_handler(
        Exception,
        unexpected_error_handler,
    )
    application.include_router(api_router)

    return application


async def _application_error_handler(
    request: Request,
    exc: Exception,
) -> Response:
    """Adapt the application error handler to Starlette's handler contract."""
    if not isinstance(exc, ApplicationError):
        raise TypeError("Expected ApplicationError.")

    return await application_error_handler(request, exc)


app = create_app()
