from datetime import datetime

from app.models.comic import Chapter, Comic, ComicStatus, SourceCapabilities
from app.sources.base import InvalidSourceUrl


class FakeSourceAdapter:
    name = "Fake"
    domains: list[str] = []
    capabilities = SourceCapabilities(
        metadata=True,
        cover=False,
        chapter_list=True,
        page_download=True,
        languages=["en"],
        supports_refresh=False,
        supports_search=False,
        requires_javascript=False,
        requires_auth=False,
    )

    def __init__(self, pages: list[str] | None = None) -> None:
        self.pages = pages or ["https://fake.local/pages/001.jpg"]

    def can_handle(self, url: str) -> bool:
        return url.startswith("fake://")

    def get_source_id(self, url: str) -> str:
        if not self.can_handle(url):
            raise InvalidSourceUrl("Enter a valid fake source URL.")
        return url.removeprefix("fake://").strip("/") or "fake"

    async def fetch_comic(self, url: str) -> Comic:
        source_id = self.get_source_id(url)
        now = datetime.utcnow()
        return Comic(
            comic_id=f"fake-{source_id}",
            title="Fake Comic",
            source=self.name,
            source_url=url,
            source_id=source_id,
            status=ComicStatus.pending,
            chapters=[
                Chapter(
                    chapter_id="chapter-001",
                    source_chapter_id="fake-chapter-001",
                    title="Fake Chapter",
                    chapter_number="1",
                    pages=len(self.pages),
                )
            ],
            created_at=now,
            updated_at=now,
        )

    async def get_chapter_pages(self, comic: Comic, chapter: Chapter) -> list[str]:
        return self.pages
