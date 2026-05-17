from typing import Protocol

from app.models.comic import Comic


class SourceError(Exception):
    """Base exception for source adapter failures."""


class InvalidSourceUrl(SourceError):
    """Raised when a URL cannot be parsed for a supported source."""


class UnsupportedSource(SourceError):
    """Raised when no source adapter can handle a URL."""


class SourceNotFound(SourceError):
    """Raised when the source cannot find the requested title."""


class SourceApiError(SourceError):
    """Raised when a source API request fails."""


class SourceAdapter(Protocol):
    name: str

    def can_handle(self, url: str) -> bool:
        """Return True when this adapter supports the URL."""

    def get_source_id(self, url: str) -> str:
        """Extract the provider-specific title identifier from the URL."""

    async def fetch_comic(self, url: str) -> Comic:
        """Fetch and normalize comic metadata from the source."""

    async def get_chapter_pages(self, chapter_id: str) -> list[str]:
        """Return remote page image URLs for a chapter."""
