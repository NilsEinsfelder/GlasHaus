"""Main application module for the GlasHaus backend."""

from fastapi import FastAPI

app = FastAPI(title="GlasHaus Backend")


@app.get("/")
def health_check() -> dict[str, str]:
    """Return the current health status of the backend."""
    return {"status": "GlasHaus backend running"}
