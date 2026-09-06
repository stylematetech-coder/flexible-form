from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ORIGINS
from .db import ensure_indexes
from .seed import seed_demo
from .routers import schemas, public


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_indexes()
    seed_demo(force=False)
    yield


app = FastAPI(title="form-service", version="1.0.0", lifespan=lifespan)

origins = ["*"] if CORS_ORIGINS == "*" else [o.strip() for o in CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(schemas.router)
app.include_router(public.router)


@app.get("/health")
def health():
    return {"ok": True}
