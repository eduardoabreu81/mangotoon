"""Settings API endpoints."""

from fastapi import APIRouter, HTTPException

from app.models.comic import Settings
from app.services.storage import load_settings, save_settings

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=Settings)
async def get_settings() -> Settings:
    data = load_settings()
    return Settings(**data)


@router.post("", response_model=Settings)
async def update_settings(payload: Settings) -> Settings:
    try:
        save_settings(payload.model_dump())
        return payload
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to save settings: {e}")
