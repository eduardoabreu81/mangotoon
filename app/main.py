from contextlib import asynccontextmanager
from pathlib import Path
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.core.config import settings
from app.routers.downloads import router as downloads_router
from app.routers.history import router as history_router
from app.routers.library import router as library_router
from app.routers.reader import router as reader_router
from app.routers.settings import router as settings_router
from app.routers.sources import router as sources_router
from app.services.download_manager import download_manager

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    download_manager.start(concurrency=2, rate_limit=1.0)
    yield
    await download_manager.stop()


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=__version__, lifespan=lifespan)

    if FRONTEND_DIR.exists():
        app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    app.include_router(library_router, prefix="/api")
    app.include_router(settings_router, prefix="/api")
    app.include_router(downloads_router, prefix="/api")
    app.include_router(reader_router, prefix="/api")
    app.include_router(history_router, prefix="/api")
    app.include_router(sources_router, prefix="/api")

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "app": settings.app_name, "version": __version__}

    @app.get("/")
    async def root() -> HTMLResponse:
        content = (FRONTEND_DIR / "index.html").read_text()
        return HTMLResponse(content=content, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

    @app.get("/reader")
    async def reader_page() -> HTMLResponse:
        content = (FRONTEND_DIR / "reader.html").read_text()
        return HTMLResponse(content=content, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

    @app.get("/comic")
    async def comic_page() -> HTMLResponse:
        content = (FRONTEND_DIR / "comic.html").read_text()
        return HTMLResponse(content=content, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

    @app.get("/settings")
    async def settings_page(request: Request) -> HTMLResponse:
        content = (FRONTEND_DIR / "settings.html").read_text()
        return HTMLResponse(content=content, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

    @app.get("/history")
    async def history_page() -> HTMLResponse:
        content = (FRONTEND_DIR / "history.html").read_text()
        return HTMLResponse(content=content, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

    @app.get("/favicon.ico")
    async def favicon() -> FileResponse:
        return FileResponse(FRONTEND_DIR / "favicon.svg")

    return app


app = create_app()
