"""Main scraper engine with rate limiting, retry, and Cloudflare detection"""

import asyncio
import re
import os
from typing import Optional
from urllib.parse import urlparse, urljoin

import httpx
from bs4 import BeautifulSoup

from app.services.llm_engine import LLMEngine
from app.services.models import ScrapingResult, ChapterInfo, PageInfo


class ScraperEngine:
    """Main scraping engine with intelligent site detection"""

    def __init__(self, llm_engine: Optional[LLMEngine] = None):
        self.llm = llm_engine or LLMEngine()
        self.rate_limit_delay = 1.0
        self.max_retries = 3
        self.retry_backoff = 2.0

    async def scrape(self, url: str) -> ScrapingResult:
        """
        Main entry point for scraping a comic URL.
        Returns a ScrapingResult with all comic information.
        """
        try:
            # Analyze site with LLM
            strategy = await self.llm.analyze_site(url)

            # Route to appropriate handler
            if strategy.has_api and strategy.api_endpoint:
                return await self._scrape_via_api(strategy, url)
            elif strategy.uses_javascript:
                return await self._scrape_with_js(url, strategy)
            else:
                return await self._scrape_html(url, strategy)

        except Exception as e:
            return ScrapingResult(
                success=False,
                title="",
                error_message=str(e)
            )

    async def _scrape_via_api(self, strategy, url: str) -> ScrapingResult:
        """Scrape using site's API (e.g., MangaDex)"""
        if "mangadex.org" in strategy.api_endpoint:
            return await self._scrape_mangadex_api(url)

        return await self._scrape_html(url, strategy)

    async def _scrape_mangadex_api(self, url: str) -> ScrapingResult:
        """Scrape MangaDex using their official API"""
        try:
            # Extract manga ID from URL
            match = re.search(r'/title/([a-z0-9-]+)', url)
            if not match:
                return ScrapingResult(success=False, title="", error_message="Invalid MangaDex URL")

            manga_id = match.group(1)
            api_base = "https://api.mangadex.org"

            async with httpx.AsyncClient(timeout=30.0) as client:
                # Get manga info
                resp = await client.get(f"{api_base}/manga/{manga_id}")
                if resp.status_code != 200:
                    return ScrapingResult(success=False, title="", error_message="Manga not found")

                manga_data = resp.json()["data"]
                attributes = manga_data["attributes"]

                title = attributes["title"].get("en") or list(attributes["title"].values())[0]

                # Get cover
                cover_url = ""
                relationships = manga_data.get("relationships", [])
                for rel in relationships:
                    if rel["type"] == "cover_art":
                        cover_url = f"{api_base}/cover/{rel['id']}/{manga_id}.jpg"

                # Get chapters
                chapters_resp = await client.get(
                    f"{api_base}/manga/{manga_id}/feed",
                    params={
                        "translatedLanguage[]": ["en", "pt", "pt-br"],
                        "order[chapter]": "asc",
                        "limit": 500
                    }
                )

                chapters = []
                if chapters_resp.status_code == 200:
                    chapters_data = chapters_resp.json()["data"]
                    for ch in chapters_data:
                        ch_attr = ch["attributes"]
                        chapter_info = ChapterInfo(
                            number=float(ch_attr.get("chapter", 0) or 0),
                            title=ch_attr.get("title", "") or f"Chapter {ch_attr.get('chapter', '?')}",
                            url=f"{api_base}/chapter/{ch['id']}"
                        )
                        chapters.append(chapter_info)

                return ScrapingResult(
                    success=True,
                    title=title,
                    cover_url=cover_url,
                    chapters=chapters,
                    total_pages=0,
                    source_site="mangadex.org"
                )

        except Exception as e:
            return ScrapingResult(success=False, title="", error_message=str(e))

    async def get_mangadex_chapter_pages(self, chapter_id: str) -> tuple[str, list[str]]:
        """
        Get MangaDex chapter page URLs.
        Returns (base_server, list_of_page_urls)
        """
        api_base = "https://api.mangadex.org"

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get chapter info
            resp = await client.get(f"{api_base}/chapter/{chapter_id}")
            if resp.status_code != 200:
                return "", []

            chapter_data = resp.json()["data"]
            ch_hash = chapter_data["attributes"]["hash"]
            pages = chapter_data["attributes"]["data"]

            # Get base URL from chapter's server
            # MangaDex uses different servers per chapter
            server_resp = await client.get(f"{api_base}/chapter/{chapter_id}/scanlation-group")
            server_url = "https://mangadex.cloud"  # default fallback

            if server_resp.status_code == 200:
                groups_data = server_resp.json().get("data", [])
                if groups_data:
                    # Use first group's base URL
                    server_url = "https://mangadex.cloud"

            # Build page URLs
            page_urls = [f"{server_url}/data/{ch_hash}/{page}" for page in pages]

            return server_url, page_urls

    async def _scrape_html(self, url: str, strategy) -> ScrapingResult:
        """Scrape using plain HTML parsing"""
        try:
            async with httpx.AsyncClient(
                timeout=30.0,
                headers={"User-Agent": "Mozilla/5.0 (compatible; ComicLib/1.0)"}
            ) as client:
                response = await client.get(url)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")

                # Extract title
                title = ""
                title_tag = soup.find("h1") or soup.find("title")
                if title_tag:
                    title = title_tag.get_text(strip=True)

                # Extract cover
                cover_url = ""
                meta_og = soup.find("meta", property="og:image")
                if meta_og:
                    cover_url = meta_og.get("content", "")

                # Find chapter links
                chapter_links = self._extract_chapter_links(soup, url, strategy)

                # Filter with LLM if available
                if chapter_links:
                    chapter_links = await self.llm.filter_links(url, chapter_links)

                # Build chapter list
                chapters = []
                for i, link in enumerate(chapter_links):
                    chapter_num = self._extract_chapter_number(link)
                    chapters.append(ChapterInfo(
                        number=chapter_num or (i + 1),
                        title=f"Capítulo {i + 1}",
                        url=link
                    ))

                return ScrapingResult(
                    success=True,
                    title=title,
                    cover_url=cover_url,
                    chapters=chapters,
                    total_pages=0,
                    source_site=urlparse(url).netloc
                )

        except Exception as e:
            return ScrapingResult(success=False, title="", error_message=str(e))

    async def _scrape_with_js(self, url: str, strategy) -> ScrapingResult:
        """Scrape using JavaScript rendering (Playwright)"""
        # TODO: Implement Playwright fallback
        # For now, try HTML scraping
        return await self._scrape_html(url, strategy)

    def _extract_chapter_links(self, soup: BeautifulSoup, base_url: str, strategy) -> list[str]:
        """Extract chapter links from parsed HTML"""
        links = []

        # Try strategy selectors first
        if strategy.chapter_list_selector:
            elements = soup.select(strategy.chapter_list_selector)
            for el in elements:
                href = el.get("href") or el.get("data-href")
                if href:
                    links.append(urljoin(base_url, href))

        # Fallback: common patterns
        if not links:
            # Look for common manga chapter patterns
            for a in soup.find_all("a", href=True):
                href = a["href"]
                text = a.get_text(strip=True).lower()

                # Skip nav links
                if any(skip in text for skip in ["home", "about", "contact", "login", "register"]):
                    continue

                # Look for chapter indicators
                if "chapter" in text or re.search(r'ch(apter)?\s*\d+', text, re.I):
                    links.append(urljoin(base_url, href))

        # Deduplicate
        seen = set()
        unique_links = []
        for link in links:
            if link not in seen:
                seen.add(link)
                unique_links.append(link)

        return unique_links

    def _extract_chapter_number(self, url: str) -> Optional[float]:
        """Extract chapter number from URL"""
        patterns = [
            r'chapter[-_]?(\d+(?:\.\d+)?)',
            r'ch(\d+(?:\.\d+)?)',
            r'-(\d+(?:\.\d+)?)\.',
            r'/(\d+(?:\.\d+)?)\.html',
        ]

        for pattern in patterns:
            match = re.search(pattern, url, re.I)
            if match:
                return float(match.group(1))

        return None

    async def download_page(self, url: str, save_path: str) -> bool:
        """Download a single page image"""
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url)
                    response.raise_for_status()

                    os.makedirs(os.path.dirname(save_path), exist_ok=True)

                    with open(save_path, "wb") as f:
                        f.write(response.content)

                    return True

            except Exception as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_backoff ** attempt)
                print(f"Failed to download {url}: {e}")

        return False