import re
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

import httpx

from app.models.comic import Chapter, Comic, ComicStatus, SourceCapabilities
from app.sources.base import InvalidSourceUrl, SourceApiError, SourceNotFound


MANGADEX_API_BASE = "https://api.mangadex.org"
MANGADEX_UPLOADS_BASE = "https://uploads.mangadex.org"
MANGADEX_TITLE_RE = re.compile(
    r"^/(?:title|manga)/(?P<title_id>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})(?:/.*)?/?$"
)


class MangaDexAdapter:
    name = "MangaDex"
    domains = ["mangadex.org", "www.mangadex.org"]
    capabilities = SourceCapabilities(
        metadata=True,
        cover=True,
        chapter_list=True,
        page_download=True,
        languages=["en"],
        supports_refresh=True,
        supports_search=False,
        requires_javascript=False,
        requires_auth=False,
    )

    def __init__(self, client: httpx.AsyncClient | None = None, api_base: str = MANGADEX_API_BASE) -> None:
        self._client = client
        self.api_base = api_base.rstrip("/")

    def can_handle(self, url: str) -> bool:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if host not in self.domains:
            return False
        return MANGADEX_TITLE_RE.match(parsed.path) is not None

    def get_source_id(self, url: str) -> str:
        parsed = urlparse(url)
        match = MANGADEX_TITLE_RE.match(parsed.path)
        if not match:
            raise InvalidSourceUrl("Enter a valid MangaDex title URL.")
        return match.group("title_id").lower()

    async def fetch_comic(self, url: str) -> Comic:
        title_id = self.get_source_id(url)
        close_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=20.0)

        try:
            manga_payload = await self._get_json(
                client,
                f"/manga/{title_id}",
                params={"includes[]": "cover_art"},
            )
            manga_data = manga_payload.get("data")
            if not manga_data:
                raise SourceNotFound("MangaDex title was not found.")

            chapters = await self._fetch_chapters(client, title_id)
            return self._normalize_comic(url, title_id, manga_data, chapters)
        finally:
            if close_client:
                await client.aclose()

    async def get_chapter_pages(self, comic: Comic, chapter: Chapter) -> list[str]:
        chapter_id = chapter.source_chapter_id or chapter.chapter_id
        close_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=20.0)

        try:
            payload = await self._get_json(client, f"/at-home/server/{chapter_id}", params={})
            base_url = payload["baseUrl"]
            chapter = payload["chapter"]
            return [f"{base_url}/data/{chapter['hash']}/{page}" for page in chapter["data"]]
        finally:
            if close_client:
                await client.aclose()

    async def _fetch_chapters(self, client: httpx.AsyncClient, title_id: str) -> list[dict[str, Any]]:
        chapters: list[dict[str, Any]] = []
        offset = 0
        limit = 100

        while True:
            payload = await self._get_json(
                client,
                f"/manga/{title_id}/feed",
                params={
                    "translatedLanguage[]": "en",
                    "order[volume]": "asc",
                    "order[chapter]": "asc",
                    "limit": limit,
                    "offset": offset,
                },
            )
            batch = payload.get("data", [])
            chapters.extend(batch)

            total = int(payload.get("total", len(chapters)))
            offset += len(batch)
            if not batch or offset >= total:
                break

        return chapters

    async def _get_json(self, client: httpx.AsyncClient, path: str, params: dict[str, Any]) -> dict[str, Any]:
        try:
            response = await client.get(f"{self.api_base}{path}", params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise SourceNotFound("MangaDex title was not found.") from exc
            raise SourceApiError(f"MangaDex API returned HTTP {exc.response.status_code}.") from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise SourceApiError("MangaDex API request failed.") from exc

    def _normalize_comic(
        self,
        url: str,
        title_id: str,
        manga_data: dict[str, Any],
        chapter_data: list[dict[str, Any]],
    ) -> Comic:
        attributes = manga_data.get("attributes", {})
        title = self._pick_localized(attributes.get("title", {})) or "Untitled Manga"
        description = self._pick_localized(attributes.get("description", {}))
        cover_url = self._cover_url(title_id, manga_data.get("relationships", []))
        now = datetime.utcnow()

        chapters = [
            self._normalize_chapter(chapter)
            for chapter in chapter_data
            if chapter.get("type") == "chapter"
        ]

        return Comic(
            comic_id=f"mangadex-{title_id}",
            title=title,
            source=self.name,
            source_url=url,
            source_id=title_id,
            description=description,
            cover_url=cover_url,
            status=ComicStatus.pending,
            chapters=chapters,
            created_at=now,
            updated_at=now,
        )

    def _normalize_chapter(self, chapter_data: dict[str, Any]) -> Chapter:
        attributes = chapter_data.get("attributes", {})
        return Chapter(
            chapter_id=chapter_data["id"],
            source_chapter_id=chapter_data["id"],
            title=attributes.get("title") or "",
            chapter_number=str(attributes.get("chapter") or ""),
            volume=str(attributes.get("volume") or ""),
            language=attributes.get("translatedLanguage") or "en",
            pages=int(attributes.get("pages") or 0),
        )

    def _cover_url(self, title_id: str, relationships: list[dict[str, Any]]) -> str:
        for relationship in relationships:
            if relationship.get("type") != "cover_art":
                continue
            file_name = relationship.get("attributes", {}).get("fileName")
            if file_name:
                return f"{MANGADEX_UPLOADS_BASE}/covers/{title_id}/{file_name}.256.jpg"
        return ""

    def _pick_localized(self, values: dict[str, str]) -> str:
        if not values:
            return ""
        return values.get("en") or next(iter(values.values()), "")
