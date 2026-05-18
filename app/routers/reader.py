"""Offline reader endpoints."""

import logging
import re
import time
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.services import storage

router = APIRouter(prefix="/reader", tags=["reader"])
logger = logging.getLogger(__name__)

SAFE_ID_RE = re.compile(r"^[\w-]+$")

_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".avif"}

_MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".avif": "image/avif",
}


class SaveProgressRequest(BaseModel):
    chapter_id: str
    page: int
    total_pages: int
    completed: bool = False


def _chapter_files_from_dir(comic_id: str, chapter_id: str) -> list[Path]:
    """List image files directly from chapter directory — no metadata read."""
    comics_root = storage.COMICS_DIR.resolve()
    chapter_dir = (storage.COMICS_DIR / comic_id / "chapters" / chapter_id).resolve()
    if not chapter_dir.is_relative_to(comics_root) or not chapter_dir.exists():
        return []
    files = [
        path for path in chapter_dir.iterdir()
        if path.is_file() and path.suffix.lower() in _IMAGE_EXTS
    ]
    files.sort(key=lambda p: p.name)
    return files


def _media_type_for(path: Path) -> str:
    return _MEDIA_TYPES.get(path.suffix.lower(), "application/octet-stream")


@router.get("/{comic_id}/data")
async def get_reader_data(comic_id: str) -> dict:
    meta = storage.load_comic_metadata(comic_id)
    if not meta:
        raise HTTPException(status_code=404, detail=f"Comic '{comic_id}' not found.")

    chapters = []
    for chapter in meta.get("chapters", []):
        if chapter.get("status") != "downloaded":
            continue
        pages = _chapter_page_paths(comic_id, chapter)
        chapters.append(
            {
                "chapter_id": chapter.get("chapter_id", ""),
                "chapter_number": chapter.get("chapter_number", ""),
                "title": chapter.get("title", ""),
                "pages": len(pages),
                "volume": chapter.get("volume", ""),
            }
        )

    return {
        "comic_id": comic_id,
        "title": meta.get("title", ""),
        "chapters": chapters,
        "progress": meta.get("reading_progress"),
    }


@router.get("/{comic_id}")
async def get_reader_chapters(comic_id: str) -> dict:
    meta = storage.load_comic_metadata(comic_id)
    if not meta:
        raise HTTPException(status_code=404, detail=f"Comic '{comic_id}' not found.")

    return {
        "comic_id": comic_id,
        "title": meta.get("title", ""),
        "chapters": [_reader_chapter_summary(comic_id, chapter) for chapter in meta.get("chapters", [])],
        "progress": meta.get("reading_progress"),
    }


@router.get("/{comic_id}/{chapter_id}/{page_number}")
async def get_page_image(comic_id: str, chapter_id: str, page_number: int) -> FileResponse:
    t0 = time.perf_counter()

    if not SAFE_ID_RE.match(comic_id) or not SAFE_ID_RE.match(chapter_id):
        raise HTTPException(status_code=400, detail="Invalid comic or chapter ID")
    if page_number < 1:
        raise HTTPException(status_code=400, detail="Page number must be >= 1")

    pages = _chapter_files_from_dir(comic_id, chapter_id)
    index = page_number - 1
    if index < 0 or index >= len(pages):
        raise HTTPException(status_code=404, detail="Page not found")

    page_path = pages[index]
    if not page_path.exists():
        raise HTTPException(status_code=404, detail="Page not found")

    resolve_ms = (time.perf_counter() - t0) * 1000
    file_size = page_path.stat().st_size

    logger.info(
        "Reader image served: comic=%s chapter=%s page=%s size=%s resolve_ms=%.2f",
        comic_id, chapter_id, page_number, file_size, resolve_ms,
    )

    return FileResponse(
        page_path,
        media_type=_media_type_for(page_path),
        headers={
            "Cache-Control": "public, max-age=3600",
            "X-MangoToon-File-Size": str(file_size),
            "X-MangoToon-Source": "direct-local-file",
        },
    )


@router.get("/{comic_id}/{chapter_id}/{page_number}/debug")
async def get_page_image_debug(comic_id: str, chapter_id: str, page_number: int) -> dict:
    t0 = time.perf_counter()

    if not SAFE_ID_RE.match(comic_id) or not SAFE_ID_RE.match(chapter_id):
        raise HTTPException(status_code=400, detail="Invalid comic or chapter ID")
    if page_number < 1:
        raise HTTPException(status_code=400, detail="Page number must be >= 1")

    pages = _chapter_files_from_dir(comic_id, chapter_id)
    index = page_number - 1
    page_path = pages[index] if 0 <= index < len(pages) else None
    resolve_ms = (time.perf_counter() - t0) * 1000

    return {
        "resolved_path": str(page_path) if page_path else None,
        "exists": page_path.exists() if page_path else False,
        "file_size_bytes": page_path.stat().st_size if page_path and page_path.exists() else 0,
        "suffix": page_path.suffix if page_path else None,
        "page_index": index,
        "local_file_count": len(pages),
        "resolve_ms": round(resolve_ms, 2),
        "source": "direct-local-file",
    }


def _chapter_page_paths(comic_id: str, chapter: dict) -> list:
    local_pages = chapter.get("local_pages") or []
    if local_pages:
        pages = []
        comics_root = storage.COMICS_DIR.resolve()
        data_root = storage.COMICS_DIR.parent.resolve()
        for page in local_pages:
            page_path = (data_root / page).resolve()
            if page_path.is_relative_to(comics_root) and page_path.is_file():
                pages.append(page_path)
        return pages
    return _fallback_chapter_pages(comic_id, chapter.get("chapter_id", ""))


def _reader_chapter_summary(comic_id: str, chapter: dict) -> dict:
    status = chapter.get("status", "not_downloaded")
    pages = _chapter_page_paths(comic_id, chapter) if status == "downloaded" else []
    return {
        "chapter_id": chapter.get("chapter_id", ""),
        "chapter_number": chapter.get("chapter_number", ""),
        "title": chapter.get("title", ""),
        "pages": len(pages) if pages else chapter.get("pages", 0),
        "volume": chapter.get("volume", ""),
        "status": status,
        "downloaded_pages": chapter.get("downloaded_pages", 0),
    }


def _fallback_chapter_pages(comic_id: str, chapter_id: str) -> list:
    chapter_dir = storage.COMICS_DIR / comic_id / "chapters" / chapter_id
    return sorted(path for path in chapter_dir.glob("*") if path.is_file()) if chapter_dir.exists() else []


@router.get("/{comic_id}/progress")
async def get_progress(comic_id: str) -> dict:
    meta = storage.load_comic_metadata(comic_id)
    if not meta:
        raise HTTPException(status_code=404, detail=f"Comic '{comic_id}' not found.")

    progress = meta.get("reading_progress") or {}
    return {
        "comic_id": comic_id,
        "chapter_id": progress.get("chapter_id", ""),
        "page": progress.get("page", 1),
        "total_pages": progress.get("total_pages", 0),
        "updated_at": progress.get("updated_at", ""),
    }


@router.post("/{comic_id}/progress")
async def save_progress(comic_id: str, payload: SaveProgressRequest) -> dict:
    meta = storage.load_comic_metadata(comic_id)
    if not meta:
        raise HTTPException(status_code=404, detail=f"Comic '{comic_id}' not found.")

    progress = {
        "chapter_id": payload.chapter_id,
        "page": payload.page,
        "total_pages": payload.total_pages,
        "updated_at": datetime.now(UTC).isoformat(),
    }
    meta["reading_progress"] = progress

    if payload.completed:
        completed = meta.setdefault("completed_chapters", [])
        if payload.chapter_id not in completed:
            completed.append(payload.chapter_id)

    storage.save_comic_metadata(comic_id, meta)

    # Isolate history update — don't let it break progress saving
    try:
        _update_history(comic_id, meta, payload.chapter_id, payload.page)
    except Exception as exc:
        logger.warning(
            "History update failed for comic=%s chapter=%s page=%s: %s",
            comic_id,
            payload.chapter_id,
            payload.page,
            exc,
        )

    return {"ok": True, "progress": progress}


def _update_history(comic_id: str, meta: dict, chapter_id: str, page: int) -> None:
    history = storage.load_history()
    items = history.get("items", [])
    items = [item for item in items if item.get("comic_id") != comic_id]
    chapter_info = next(
        (chapter for chapter in meta.get("chapters", []) if chapter.get("chapter_id") == chapter_id),
        {},
    )
    # Guard against None chapter_info
    chapter_number = chapter_info.get("chapter_number", "") if chapter_info else ""
    items.insert(
        0,
        {
            "comic_id": comic_id,
            "title": meta.get("title", ""),
            "cover_path": str(storage.COMICS_DIR / comic_id / "cover.jpg"),
            "chapter_id": chapter_id,
            "chapter_number": chapter_number,
            "page_number": page,
            "last_read_at": datetime.now(UTC).isoformat(),
        },
    )
    history["items"] = items[:20]
    storage.save_history(history)
