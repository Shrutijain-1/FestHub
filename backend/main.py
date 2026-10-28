"""Entry point of the FastAPI backend."""
import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from backend.core.config import APP_NAME
from backend.routes import ai, auth, colleges, dashboard, events, organizer, registrations

logger = logging.getLogger("eventflow.api")

STATIC_DIR = Path(__file__).resolve().parent / "static"
(STATIC_DIR / "uploads").mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title=f"{APP_NAME} API",
    description="REST API for college event discovery and management",
    version="0.1.0",
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(auth.router)
app.include_router(events.router)
app.include_router(organizer.router)
app.include_router(registrations.router)
app.include_router(ai.router)
app.include_router(colleges.router)
app.include_router(dashboard.router)


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(request: Request, error: SQLAlchemyError):
    """Any database failure becomes a friendly message. The details go to the log."""
    logger.exception("Database error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=503,
        content={"detail": "A database problem occurred. Please try again."},
    )


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, error: Exception):
    """Last safety net: users never see a raw Python error."""
    logger.exception("Unexpected error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Something went wrong on our side. Please try again."},
    )


@app.get("/api/health")
def health_check() -> dict:
    """Used by the frontend to check that the backend is running."""
    return {"status": "ok", "app": APP_NAME}