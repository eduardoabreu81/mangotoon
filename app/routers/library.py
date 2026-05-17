"""Library API endpoints."""

import asyncio
from urllib.parse import urlparse
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.models.comic import Comic, LibraryResponse
from app.services.download_manager import download_manager
from app.services.source_registry import source_registry
from app.services.storage import (
    add_comic,
    delete_comic,
    get_comic,
    load_comic_metadata,
    load_library,
    save_comic_metadata,
    save_library,
)
from app.sources.base import InvalidSourceUrl, SourceApiError, SourceNotFound, UnsupportedSource

router = APIRouter(prefix="/library", tags=["library"])


class AddComicRequest(BaseModel):
    url: str


class AddComicResponse(BaseModel):
    comic: Comic
    duplicate: bool = False


class UpdateComicStatusRequest(BaseModel):
    status: Literal["reading", "completed"]


@router.get("", response_model=LibraryResponse)
async def list_library() -> LibraryResponse:
    library = load_library()
    comics = [Comic(**c) for c in library.get("comics", [])]
    return LibraryResponse(comics=comics, total=len(comics))


@router.get("/filter", response_model=LibraryResponse)
async def filter_library(
    status: Literal["reading", "completed", "downloaded", "pending"] | None = None,
    source: str | None = None,
    sort: str = Query(default="added"),
) -> LibraryResponse:
    comics = load_library().get("comics", [])

    if status:
        comics = [comic for comic in comics if _matches_status_filter(comic, status)]
    if source:
        source_key = source.lower()
        comics = [comic for comic in comics if (comic.get("source") or "").lower() == source_key]

    comics = _sort_comics(comics, sort)
    normalized = [Comic(**comic) for comic in comics]
    return LibraryResponse(comics=normalized, total=len(normalized))


@router.post("/add", response_model=AddComicResponse)
async def add_comic_from_source(payload: AddComicRequest) -> AddComicResponse:
    url = _validate_add_url(payload.url)

    try:
        adapter = source_registry.get_adapter(url)
        source_id = adapter.get_source_id(url)
    except InvalidSourceUrl as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except UnsupportedSource as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    duplicate = _find_duplicate(url, adapter.name, source_id)
    if duplicate:
        return AddComicResponse(comic=Comic(**duplicate), duplicate=True)

    try:
        comic = await adapter.fetch_comic(url)
    except InvalidSourceUrl as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except UnsupportedSource as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SourceNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SourceApiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    comic_data = comic.model_dump(mode="json")
    add_comic(comic_data)
    save_comic_metadata(comic.comic_id, comic_data)
    asyncio.create_task(download_manager.enqueue_comic(comic.comic_id))
    return AddComicResponse(comic=comic, duplicate=False)


@router.get("/{comic_id}", response_model=Comic)
async def get_comic_detail(comic_id: str) -> Comic:
    data = get_comic(comic_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Comic '{comic_id}' not found")
    return Comic(**data)


@router.delete("/{comic_id}")
async def remove_comic(comic_id: str) -> dict[str, str]:
    if not delete_comic(comic_id):
        raise HTTPException(status_code=404, detail=f"Comic '{comic_id}' not found")
    return {"message": f"Comic '{comic_id}' deleted"}


@router.post("/{comic_id}/status", response_model=Comic)
async def update_comic_status(comic_id: str, payload: UpdateComicStatusRequest) -> Comic:
    metadata = load_comic_metadata(comic_id)
    if not metadata:
        raise HTTPException(status_code=404, detail=f"Comic '{comic_id}' not found.")

    metadata["status"] = payload.status
    save_comic_metadata(comic_id, metadata)

    library = load_library()
    found = False
    for comic in library.get("comics", []):
        if comic.get("comic_id") == comic_id:
            comic["status"] = payload.status
            found = True
            break
    if found:
        save_library(library)

    return Comic(**metadata)


@router.post("/{comic_id}/download")
async def download_comic(comic_id: str) -> dict:
    data = get_comic(comic_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Comic '{comic_id}' not found.")
    asyncio.create_task(download_manager.enqueue_comic(comic_id))
    return {"message": "Download started.", "comic_id": comic_id}


@router.post("/{comic_id}/chapters/{chapter_id}/download")
async def download_chapter(comic_id: str, chapter_id: str) -> dict:
    data = get_comic(comic_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Comic '{comic_id}' not found.")
    asyncio.create_task(download_manager.enqueue_chapter(comic_id, chapter_id))
    return {"message": "Chapter download started.", "comic_id": comic_id, "chapter_id": chapter_id}


def _validate_add_url(url: str) -> str:
    normalized = url.strip()
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(status_code=400, detail="Enter a valid HTTP or HTTPS URL.")
    return normalized


def _find_duplicate(url: str, source_name: str, source_id: str) -> dict | None:
    normalized_url = url.rstrip("/")
    for comic in load_library().get("comics", []):
        same_source = (comic.get("source") or "").lower() == source_name.lower()
        same_source_id = same_source and comic.get("source_id") == source_id
        same_url = (comic.get("source_url") or "").rstrip("/") == normalized_url
        if same_source_id or same_url:
            return comic
    return None


def _matches_status_filter(comic: dict, status: str) -> bool:
    comic_status = comic.get("status")
    if status == "completed":
        return comic_status in {"completed", "complete"}
    if status == "downloaded":
        return _downloaded_count(comic) > 0 or comic_status in {"downloaded", "complete", "completed"}
    return comic_status == status


def _sort_comics(comics: list[dict], sort: str) -> list[dict]:
    sorted_comics = list(comics)
    if sort == "title":
        sorted_comics.sort(key=lambda comic: (comic.get("title") or "").lower())
    elif sort == "updated":
        sorted_comics.sort(key=lambda comic: comic.get("updated_at") or "", reverse=True)
    elif sort == "progress":
        sorted_comics.sort(key=_download_progress, reverse=True)
    elif sort == "status":
        sorted_comics.sort(key=lambda comic: comic.get("status") or "")
    else:
        sorted_comics.sort(key=lambda comic: comic.get("created_at") or "", reverse=True)
    return sorted_comics


def _downloaded_count(comic: dict) -> int:
    if "downloaded_count" in comic:
        return int(comic.get("downloaded_count") or 0)
    return sum(1 for chapter in comic.get("chapters", []) if chapter.get("status") == "downloaded")


def _download_progress(comic: dict) -> float:
    chapters = comic.get("chapters", [])
    total = int(comic.get("chapter_count") or len(chapters) or 0)
    if total == 0:
        return 0.0
    return _downloaded_count(comic) / total
