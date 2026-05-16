"""Models for scraping operations"""

from pydantic import BaseModel, Field
from typing import Optional


class PageInfo(BaseModel):
    """Information about a single page"""
    number: int
    url: str
    local_path: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


class ChapterInfo(BaseModel):
    """Information about a chapter"""
    number: float
    title: str = ""
    url: str
    pages: list[PageInfo] = Field(default_factory=list)
    downloaded: bool = False


class ScrapingResult(BaseModel):
    """Result of a scraping operation"""
    success: bool
    title: str
    cover_url: str = ""
    chapters: list[ChapterInfo] = Field(default_factory=list)
    total_pages: int = 0
    source_site: str = ""
    error_message: Optional[str] = None


class SiteStrategy(BaseModel):
    """Strategy determined by LLM for scraping a site"""
    site_name: str
    base_url: str
    has_api: bool = False
    api_endpoint: Optional[str] = None
    uses_cloudflare: bool = False
    uses_javascript: bool = False
    chapter_list_selector: str = ""
    page_image_selector: str = ""
    sitemap_url: Optional[str] = None
    parse_instructions: str = ""