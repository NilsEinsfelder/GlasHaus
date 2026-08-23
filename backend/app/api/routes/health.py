"""Health-check API routes."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/", response_model=dict[str, str])
def health_check() -> dict[str, str]:
    """Return the current backend health status."""
    return {"status": "GlasHaus backend running"}


@router.get("/health", response_model=dict[str, str])
def health_status() -> dict[str, str]:
    """Return the current backend health status."""
    return {"status": "ok"}
