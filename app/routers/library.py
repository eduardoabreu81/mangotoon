"""Library API endpoints."""

from fastapi import APIRouter, HTTPException

from app.models.comic import Comic, LibraryResponse
from app.services.storage import add_comic, delete_comic, get_comic, load_library

router = APIRouter(prefix="/library", tags=["library"])


@router.get("", response_model=LibraryResponse)
async def list_library() -> LibraryResponse:
    library = load_library()
    comics = [Comic(**c) for c in library.get("comics", [])]
    return LibraryResponse(comics=comics, total=len(comics))


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
