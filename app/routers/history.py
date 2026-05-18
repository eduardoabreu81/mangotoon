"""History API endpoints."""

from fastapi import APIRouter, HTTPException

from app.services import storage

router = APIRouter(prefix="/history", tags=["history"])


@router.get("")
async def list_history() -> list[dict]:
    history = storage.load_history()
    # Guard against cases where load_history returns a list directly
    if isinstance(history, list):
        return history[:20]
    return history.get("items", [])[:20]


@router.delete("/{comic_id}")
async def delete_history_item(comic_id: str) -> dict[str, str]:
    history = storage.load_history()
    items = history.get("items", [])
    remaining = [item for item in items if item.get("comic_id") != comic_id]
    if len(remaining) == len(items):
        raise HTTPException(status_code=404, detail=f"Comic '{comic_id}' not found in history.")

    history["items"] = remaining
    storage.save_history(history)
    return {"message": "History item deleted.", "comic_id": comic_id}
