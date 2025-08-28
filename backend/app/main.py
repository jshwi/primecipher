from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.routes import narratives as r_narratives
from .api.routes import parents as r_parents
from .api.routes import refresh as r_refresh
from .repo import init_db
from .version import version_payload


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


def _parse_origins() -> list[str]:
    raw = (os.getenv("FRONTEND_ORIGINS") or "http://localhost:3000").strip()
    return [o.strip() for o in raw.split(",") if o.strip()]


import os
app = FastAPI(title="PrimeCipher API (MVP)", lifespan=lifespan)

# CORS (tightened; see commit 2 for details)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Standardized error envelope
@app.exception_handler(HTTPException)
async def http_exc_handler(_: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"ok": False, "error": str(exc.detail)})

@app.exception_handler(Exception)
async def unhandled_exc_handler(_: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"ok": False, "error": "internal_error"})

# Routes
app.include_router(r_narratives.router)
app.include_router(r_parents.router)
app.include_router(r_refresh.router)

@app.get("/healthz")
def health() -> dict:
    return {"ready": True}

@app.get("/readyz")
def readyz() -> dict:
    return {"ready": True}

@app.get("/version")
def version() -> dict:
    return {"version": version_payload()}

@app.get("/__boom_for_tests__")
def boom_for_tests():
    raise Exception("kaboom")
