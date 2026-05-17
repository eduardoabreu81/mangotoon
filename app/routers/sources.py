import logging

from pydantic import BaseModel

from fastapi import APIRouter

from app.models.comic import SourceCapabilities
from app.sources.base import SourceError
from app.services.source_registry import source_registry

logger = logging.getLogger(__name__)

router = APIRouter(tags=["sources"])


class DetectRequest(BaseModel):
    url: str


class DetectResponse(BaseModel):
    supported: bool
    source: str
    message: str


@router.get("/sources")
async def list_sources() -> list[dict]:
    return [
        {
            "name": adapter.name,
            "domains": getattr(adapter, "domains", []),
            "capabilities": getattr(adapter, "capabilities", SourceCapabilities()).model_dump(),
        }
        for adapter in source_registry.adapters
    ]


@router.post("/sources/detect")
async def detect_source(body: DetectRequest) -> DetectResponse:
    try:
        adapter = source_registry.get_adapter(body.url)
        return DetectResponse(
            supported=True,
            source=adapter.name,
            message=f"{adapter.name} title URL detected.",
        )
    except SourceError as exc:
        logger.debug("Source detection failed for %s: %s", body.url, exc)
        return DetectResponse(
            supported=False,
            source="",
            message="Unsupported source. Please provide a valid URL from a supported source.",
        )
