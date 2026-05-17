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
        "state": derived_status,
        "total_chapters": total,
        "downloaded_chapters": downloaded,
        "error_chapters": errors,
        "current_chapter_id": None,
    }


@router.get("")
async def list_active_downloads() -> list[dict]:
    return download_manager.list_active()


@router.get("/status")
async def list_download_statuses() -> list[dict]:
    return download_manager.list_active()


@router.post("/{comic_id}/pause")
async def pause_download(comic_id: str) -> dict:
    if not download_manager.pause_comic(comic_id):
        raise HTTPException(status_code=404, detail=f"Active download for comic '{comic_id}' not found.")
    return {"message": "Download paused.", "comic_id": comic_id, "status": "paused", "state": "paused"}


@router.post("/{comic_id}/resume")
async def resume_download(comic_id: str) -> dict:
    if not download_manager.resume_comic(comic_id):
        raise HTTPException(status_code=404, detail=f"Paused download for comic '{comic_id}' not found.")
    return {"message": "Download resumed.", "comic_id": comic_id, "status": "queued", "state": "queued"}


@router.post("/{comic_id}/cancel")
async def cancel_download(comic_id: str) -> dict:
    if not download_manager.cancel_comic(comic_id):
        raise HTTPException(status_code=404, detail=f"Download for comic '{comic_id}' not found.")
    return {
        "message": "Download cancelled.",
        "comic_id": comic_id,
        "status": "cancelled",
        "state": "cancelled",
    }


@router.post("/{comic_id}/chapters/{chapter_id}/retry")
async def retry_chapter_download(comic_id: str, chapter_id: str) -> dict:
    if not await download_manager.retry_chapter(comic_id, chapter_id):
        raise HTTPException(
            status_code=404,
            detail=f"Failed chapter '{chapter_id}' for comic '{comic_id}' not found.",
        )
    return {
        "message": "Chapter retry queued.",
        "comic_id": comic_id,
        "chapter_id": chapter_id,
        "status": "queued",
        "state": "queued",
    }
