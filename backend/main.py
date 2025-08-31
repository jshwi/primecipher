"""FastAPI application main module."""

import os
import typing as t
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from .api.routes import narratives as r_narratives
from .api.routes import parents as r_parents
from .api.routes import refresh as r_refresh
from .api.routes import refresh_jobs as r_refresh_jobs
from .repo import init_db
from .version import version_payload


@asynccontextmanager
async def lifespan(_: FastAPI) -> t.AsyncGenerator[None, None]:
    """Application lifespan manager for database initialization.

    :param _: FastAPI app instance (unused).
    :yield: None.
    """
    init_db()
    yield


def _parse_origins() -> list[str]:
    raw = (os.getenv("FRONTEND_ORIGINS") or "http://localhost:3000").strip()
    return [o.strip() for o in raw.split(",") if o.strip()]


app = FastAPI(title="PrimeCipher API (MVP)", lifespan=lifespan)

# cors (tightened; see commit 2 for details)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# prometheus metrics at /metrics (exclude noise)
Instrumentator(
    should_group_status_codes=False,
    excluded_handlers=["/metrics", "/healthz", "/readyz"],
).instrument(app).expose(app, include_in_schema=False)


# standardized error envelope
@app.exception_handler(HTTPException)
async def http_exc_handler(_: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions with standardized error envelope.

    :param _: The request object.
    :param exc: The HTTP exception.
    :return: Standardized error envelope.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"ok": False, "error": str(exc.detail)},
    )


@app.exception_handler(Exception)
async def unhandled_exc_handler(_: Request, _exc: Exception) -> JSONResponse:
    """Handle unhandled exceptions with standardized error envelope.

    :return: Standardized error envelope.
    """
    return JSONResponse(
        status_code=500,
        content={"ok": False, "error": "internal_error"},
    )


# routes
app.include_router(r_narratives.router)
app.include_router(r_parents.router)
app.include_router(r_refresh.router)
app.include_router(r_refresh_jobs.router)


@app.get("/healthz")
def health() -> dict:
    """Health check endpoint.

    :return: Health status.
    """
    return {"ready": True}


@app.get("/readyz")
def readyz() -> dict:
    """Readiness check endpoint.

    :return: Readiness status.
    """
    return {"ready": True}


@app.get("/version")
def version() -> dict:
    """Version information endpoint.

    :return: Version information.
    """
    return {"version": version_payload()}


@app.get("/__boom_for_tests__")
def boom_for_tests() -> None:
    """Test endpoint that raises an exception."""
    raise RuntimeError("kaboom")
