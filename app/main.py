from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers.library import router as library_router

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings.library_path.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="ComicLib",
    version="0.1.0",
    description="Comic Library Downloader — Baixe e leia quadrinhos offline",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(library_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
