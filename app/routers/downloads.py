"""Download status endpoints."""

from fastapi import APIRouter, HTTPException

from app.services.download_manager import download_manager
from app.services.storage import load_comic_metadata

router = APIRouter(prefix="/downloads", tags=["downloads"])


@router.get("/{comic_id}/status")
async def get_download_status(comic_id: str) -> dict:
    status = download_manager.get_status(comic_id)
    if status:
        return status

    meta = load_comic_metadata(comic_id)
    if not meta:
        raise HTTPException(status_code=404, detail=f"Comic '{comic_id}' not found.")

    chapters = meta.get("chapters", [])
    total = len(chapters)
    downloaded = sum(1 for chapter in chapters if chapter.get("status") == "downloaded")
    errors = sum(1 for chapter in chapters if chapter.get("status") == "error")
    if total == 0 or downloaded == 0 and errors == 0:
        derived_status = meta.get("status", "pending")
    elif downloaded == total:
        derived_status = "complete"
    elif errors == total:
        derived_status = "error"
    elif downloaded + errors == total:
        derived_status = "partial"
    else:
        derived_status = meta.get("status", "partial")

    return {
        "comic_id": comic_id,
        "status": derived_status,
        "total_chapters": total,
        "downloaded_chapters": downloaded,
        "error_chapters": errors,
        "current_chapter_id": None,
    }


@router.get("")
async def list_active_downloads() -> list[dict]:
    return download_manager.list_active()
