"""Offline reader endpoints."""

import re
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.services import storage

router = APIRouter(prefix="/reader", tags=["reader"])

SAFE_ID_RE = re.compile(r"^[\w-]+$")


class SaveProgressRequest(BaseModel):
    chapter_id: str
    page: int
    total_pages: int
    completed: bool = False


@router.get("/{comic_id}/data")
async def get_reader_data(comic_id: str) -> dict:
    meta = storage.load_comic_metadata(comic_id)
    if not meta:
        raise HTTPException(status_code=404, detail=f"Comic '{comic_id}' not found.")

    chapters = []
    for chapter in meta.get("chapters", []):
        if chapter.get("status") != "downloaded":
            continue
        chapter_dir = storage.COMICS_DIR / comic_id / "chapters" / chapter["chapter_id"]
        pages = sorted(path for path in chapter_dir.glob("*") if path.is_file()) if chapter_dir.exists() else []
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


@router.get("/{comic_id}/{chapter_id}/{page_number}")
async def get_page_image(comic_id: str, chapter_id: str, page_number: int) -> FileResponse:
    if not SAFE_ID_RE.match(comic_id) or not SAFE_ID_RE.match(chapter_id):
        raise HTTPException(status_code=400, detail="Invalid comic or chapter ID")

    comics_root = storage.COMICS_DIR.resolve()
    chapter_dir = (storage.COMICS_DIR / comic_id / "chapters" / chapter_id).resolve()
    if not chapter_dir.is_relative_to(comics_root):
        raise HTTPException(status_code=400, detail="Invalid comic or chapter ID")

    pages = sorted(path for path in chapter_dir.glob("*") if path.is_file()) if chapter_dir.exists() else []
    index = page_number - 1
    if index < 0 or index >= len(pages):
        raise HTTPException(status_code=404, detail="Page not found")

    page_path = pages[index]
    if not page_path.exists():
        raise HTTPException(status_code=404, detail="Page not found")
    return FileResponse(page_path)


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
    _update_history(comic_id, meta, payload.chapter_id, payload.page)
    return {"ok": True, "progress": progress}


def _update_history(comic_id: str, meta: dict, chapter_id: str, page: int) -> None:
    history = storage.load_history()
    items = history.get("items", [])
    items = [item for item in items if item.get("comic_id") != comic_id]
    chapter_info = next(
        (chapter for chapter in meta.get("chapters", []) if chapter.get("chapter_id") == chapter_id),
        {},
    )
    items.insert(
        0,
        {
            "comic_id": comic_id,
            "title": meta.get("title", ""),
            "cover_path": str(storage.COMICS_DIR / comic_id / "cover.jpg"),
            "chapter_id": chapter_id,
            "chapter_number": chapter_info.get("chapter_number", ""),
            "page_number": page,
            "last_read_at": datetime.now(UTC).isoformat(),
        },
    )
    history["items"] = items[:20]
    storage.save_history(history)
