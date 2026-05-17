"""Pydantic models for the manga library."""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, computed_field


class ChapterStatus(str, Enum):
    not_downloaded = "not_downloaded"
    queued = "queued"
    downloading = "downloading"
    downloaded = "downloaded"
    partial = "partial"
    cancelled = "cancelled"
    error = "error"


class Chapter(BaseModel):
    chapter_id: str
    source_chapter_id: str = ""
    title: str = ""
    chapter_number: str = ""
    volume: str = ""
    language: str = "en"
    pages: int = 0
    status: ChapterStatus = ChapterStatus.not_downloaded
    downloaded_pages: int = 0
    local_pages: list[str] = Field(default_factory=list)
    failed_pages: list[str] = Field(default_factory=list)
    error_message: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReadingProgress(BaseModel):
    comic_id: str
    chapter_id: str = ""
    page: int = 0
    total_pages: int = 0
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SourceCapabilities(BaseModel):
    metadata: bool = True
    cover: bool = True
    chapter_list: bool = True
    page_download: bool = True
    languages: list[str] = Field(default_factory=list)
    supports_refresh: bool = False
    supports_search: bool = False
    requires_javascript: bool = False
    requires_auth: bool = False


class ComicStatus(str, Enum):
    pending = "pending"
    metadata_fetching = "metadata_fetching"
    queued = "queued"
    downloading = "downloading"
    paused = "paused"
    downloaded = "downloaded"
    reading = "reading"
    completed = "completed"
    complete = "complete"
    partial = "partial"
    cancelled = "cancelled"
    error = "error"


class Comic(BaseModel):
    comic_id: str
    title: str
    source: str = ""
    source_url: str = ""
    source_id: str = ""
    description: str = ""
    cover_url: str = ""
    cover_local: str = ""
    status: ComicStatus = ComicStatus.pending
    chapters: list[Chapter] = Field(default_factory=list)
    progress: ReadingProgress | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @computed_field
    @property
    def chapter_count(self) -> int:
        return len(self.chapters)

    @computed_field
    @property
    def downloaded_count(self) -> int:
        return sum(1 for c in self.chapters if c.status == ChapterStatus.downloaded)


class ImportPreview(BaseModel):
    source: str
    source_id: str
    title: str
    description: str = ""
    cover_url: str = ""
    chapter_count: int = 0
    languages: list[str] = Field(default_factory=list)
    duplicate: bool = False
    warnings: list[str] = Field(default_factory=list)


class LibraryResponse(BaseModel):
    comics: list[Comic]
    total: int


class Settings(BaseModel):
    app_name: str = "MangoToon"
    library_path: str = "./data/comics"
    download_concurrency: int = Field(default=2, ge=1, le=5)
    rate_limit_per_domain: float = 1.0
    reader_default_fit: Literal["fit-width", "fit-height", "fit-screen", "original"] = "fit-width"
    reader_auto_advance: bool = False
    reader_auto_advance_delay: int = Field(default=4, ge=1, le=120)
    reader_show_progress_bar: bool = True
    download_auto_start: bool = True
    download_default_chapters: Literal["all", "unread", "none"] = "all"
    theme: Literal["dark", "light", "auto"] = "dark"
    language: str = "en"
    llm_provider: str = ""
    llm_model: str = ""
    llm_api_key: str = ""


class APIError(BaseModel):
    error: str
    detail: str = ""
    code: int = 400
