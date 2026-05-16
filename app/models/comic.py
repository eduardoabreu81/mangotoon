from datetime import datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class ComicStatus(str, Enum):
    pending = "pending"
    downloading = "downloading"
    complete = "complete"
    error = "error"


class Chapter(BaseModel):
    number: float
    title: str
    pages: list[str] = Field(default_factory=list)
    downloaded: bool = False
    path: str = ""


class ReadingProgress(BaseModel):
    comic_id: str
    chapter: float
    page: int
    completed: bool = False
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Comic(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    source_url: str
    source_site: str
    cover_url: str = ""
    total_chapters: int = 0
    downloaded_chapters: list[int] = Field(default_factory=list)
    status: ComicStatus = ComicStatus.pending
    last_read_chapter: int = 0
    last_read_page: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
