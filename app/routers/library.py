"""Rotas da API da biblioteca de quadrinhos"""

import asyncio
import re
from uuid import uuid4
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, field_validator

from app.core.config import settings
from app.models.comic import ComicStatus
from app.services.downloader import download_manager

# Private IP ranges to block (SSRF prevention)
PRIVATE_IP_PATTERNS = [
    r'^127\.',           # Loopback
    r'^10\.',            # Class A private
    r'^172\.(1[6-9]|2[0-9]|3[0-1])\.',  # Class B private
    r'^192\.168\.',      # Class C private
    r'^169\.254\.',      # Link-local (AWS metadata)
    r'^0\.',             # Current network
    r'^localhost$',      # Localhost hostname
]
PRIVATE_IP_RE = re.compile('|'.join(PRIVATE_IP_PATTERNS), re.IGNORECASE)


def validate_url(url: str) -> str:
    """Validate URL to prevent SSRF attacks."""
    parsed = urlparse(url)

    # Only allow HTTP and HTTPS
    if parsed.scheme not in ('http', 'https'):
        raise HTTPException(status_code=400, detail="Only HTTP/HTTPS URLs are allowed")

    # Check for private/internal hostnames
    hostname = parsed.hostname or ''
    if PRIVATE_IP_RE.match(hostname):
        raise HTTPException(status_code=400, detail="Private IP addresses are not allowed")

    # Block cloud metadata endpoints
    if hostname in ('169.254.169.254', 'metadata.google.internal', 'metadata.internal'):
        raise HTTPException(status_code=400, detail="Cloud metadata endpoints are not allowed")

    # Ensure no credentials in URL
    if parsed.username or parsed.password:
        raise HTTPException(status_code=400, detail="URLs with credentials are not allowed")

    # Block data: or other dangerous schemes
    if parsed.scheme not in ('http', 'https'):
        raise HTTPException(status_code=400, detail="Unsupported URL scheme")

    return url

router = APIRouter(prefix="/api", tags=["library"])


class AddComicRequest(BaseModel):
    url: str
    title: str = ""


class UpdateProgressRequest(BaseModel):
    chapter: float
    page: int
    completed: bool = False


@router.get("/library")
async def list_library():
    """Lista todos os quadrinhos na biblioteca."""
    return settings.load_library()


@router.get("/library/{comic_id}")
async def get_comic(comic_id: str):
    """Retorna detalhes de um quadrinho."""
    comic = settings.load_comic_metadata(comic_id)
    if not comic:
        raise HTTPException(status_code=404, detail="Quadrinho não encontrado")
    return comic


@router.post("/library/add")
async def add_comic(request: AddComicRequest):
    """Adiciona URL de um quadrinho para baixar."""
    # Validate URL to prevent SSRF
    validate_url(request.url)

    comic_id = str(uuid4())
    parsed = urlparse(request.url)

    comic_data = {
        "id": comic_id,
        "title": request.title or "Carregando...",
        "source_url": request.url,
        "source_site": parsed.netloc,
        "cover_url": "",
        "total_chapters": 0,
        "downloaded_chapters": [],
        "status": ComicStatus.pending.value,
        "last_read_chapter": 0,
        "last_read_page": 0,
        "chapters": [],
    }

    library = settings.load_library()
    library.append(comic_data)
    settings.save_library(library)

    # Save initial metadata
    settings.save_comic_metadata(comic_id, comic_data)

    # Start download in background
    asyncio.create_task(download_manager.start_download(comic_id, request.url))

    return {"comic_id": comic_id, "status": "pending"}


@router.delete("/library/{comic_id}")
async def delete_comic(comic_id: str):
    """Remove um quadrinho da biblioteca."""
    library = settings.load_library()
    new_library = [c for c in library if c.get("id") != comic_id]
    if len(new_library) == len(library):
        raise HTTPException(status_code=404, detail="Quadrinho não encontrado")

    settings.save_library(new_library)

    # Remove arquivos locais
    import shutil
    comic_path = settings.library_path / comic_id
    if comic_path.exists():
        shutil.rmtree(comic_path)

    return {"status": "deleted"}


@router.get("/reader/{comic_id}/chapters")
async def list_chapters(comic_id: str):
    """Lista capítulos de um quadrinho."""
    comic = settings.load_comic_metadata(comic_id)
    if not comic:
        raise HTTPException(status_code=404, detail="Quadrinho não encontrado")
    return comic.get("chapters", [])


@router.get("/reader/{comic_id}/{chapter}/{page}")
async def serve_page(comic_id: str, chapter: float, page: int):
    """Serve uma página de quadrinho."""
    from fastapi.responses import FileResponse

    page_path = settings.library_path / comic_id / "chapters" / str(int(chapter)) / f"{page:03d}.jpg"
    if not page_path.exists():
        # Tenta outros formatos
        for ext in ["png", "webp", "jpeg"]:
            alt_path = settings.library_path / comic_id / "chapters" / str(int(chapter)) / f"{page:03d}.{ext}"
            if alt_path.exists():
                return FileResponse(alt_path)
        raise HTTPException(status_code=404, detail="Página não encontrada")

    return FileResponse(page_path)


@router.get("/reader/{comic_id}/progress")
async def get_progress(comic_id: str):
    """Retorna progresso de leitura."""
    comic = settings.load_comic_metadata(comic_id)
    if not comic:
        raise HTTPException(status_code=404, detail="Quadrinho não encontrado")
    return comic.get("reading_progress", {})


@router.post("/reader/{comic_id}/progress")
async def update_progress(comic_id: str, request: UpdateProgressRequest):
    """Atualiza progresso de leitura."""
    comic = settings.load_comic_metadata(comic_id)
    if not comic:
        raise HTTPException(status_code=404, detail="Quadrinho não encontrado")

    comic["reading_progress"] = {
        "last_chapter": request.chapter,
        "last_page": request.page,
        "completed": request.completed,
    }
    settings.save_comic_metadata(comic_id, comic)

    return {"status": "updated"}


@router.get("/download/{comic_id}/status")
async def download_status(comic_id: str):
    """Retorna status do download."""
    comic = settings.load_comic_metadata(comic_id)
    if not comic:
        raise HTTPException(status_code=404, detail="Quadrinho não encontrado")

    return {
        "comic_id": comic_id,
        "status": comic.get("status", "unknown"),
        "downloaded_chapters": comic.get("downloaded_chapters", []),
        "total_chapters": comic.get("total_chapters", 0),
    }


@router.get("/settings")
async def get_settings():
    """Retorna configurações."""
    return {
        "library_path": str(settings.library_path),
        "scraper_concurrency": settings.scraper_concurrency,
    }


@router.post("/settings")
async def update_settings(data: dict):
    """Salva configurações."""
    # TODO: implementar persistência de configurações
    return {"status": "updated"}