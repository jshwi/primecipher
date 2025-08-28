from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import narratives as r_narratives
from .api.routes import parents as r_parents
from .api.routes import refresh as r_refresh

app = FastAPI(title="PrimeCipher API (MVP)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(r_narratives.router)
app.include_router(r_parents.router)
app.include_router(r_refresh.router)

@app.get("/healthz")
def health() -> dict:
    return {"ready": True}
