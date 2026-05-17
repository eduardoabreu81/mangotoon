"""Library API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from urllib.parse import urlparse

from app.models.comic import Comic, LibraryResponse
from app.services.source_registry import source_registry
from app.services.storage import add_comic, delete_comic, get_comic, load_library, save_comic_metadata
from app.sources.base import InvalidSourceUrl, SourceApiError, SourceNotFound, UnsupportedSource

router = APIRouter(prefix="/library", tags=["library"])


class AddComicRequest(BaseModel):
    url: str


class AddComicResponse(BaseModel):
    comic: Comic
    duplicate: bool = False


@router.get("", response_model=LibraryResponse)
async def list_library() -> LibraryResponse:
    library = load_library()
    comics = [Comic(**c) for c in library.get("comics", [])]
    return LibraryResponse(comics=comics, total=len(comics))


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
