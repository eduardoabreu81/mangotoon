"""Tests for scraper service"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.scraper import ScraperEngine
from app.services.llm_engine import LLMEngine
from app.services.models import ScrapingResult, SiteStrategy


class TestScraperEngine:
    def test_extract_chapter_number_various_formats(self):
        scraper = ScraperEngine()

        # Test various URL patterns
        assert scraper._extract_chapter_number("https://manga.com/chapter/123") == 123.0
        assert scraper._extract_chapter_number("https://manga.com/chapter-456") == 456.0
        assert scraper._extract_chapter_number("https://manga.com/ch-789") == 789.0
        assert scraper._extract_chapter_number("https://manga.com/123.html") == 123.0
        assert scraper._extract_chapter_number("https://manga.com/1.5") == 1.5
        assert scraper._extract_chapter_number("https://manga.com/no-number-here") is None

    @pytest.mark.asyncio
    async def test_scrape_mangadex_invalid_url(self):
        scraper = ScraperEngine()
        result = await scraper._scrape_mangadex_api("https://mangadex.org/title/")
        assert result.success is False
        assert "Invalid MangaDex URL" in result.error_message

    @pytest.mark.asyncio
    async def test_scrape_mangadex_fallback_on_error(self):
        scraper = ScraperEngine()
        # Test with non-existent manga - should handle gracefully
        result = await scraper._scrape_mangadex_api("https://mangadex.org/title/nonexistent-manga-id-12345")
        # This will fail but should return a proper ScrapingResult with error
        assert result.success is False


class TestLLMEngine:
    def test_extract_json_with_code_block(self):
        llm = LLMEngine()
        text = '''
        Here's the JSON you asked for:
        ```json
        {"site_name": "test", "base_url": "https://test.com", "has_api": false}
        ```
        '''
        result = llm._extract_json(text)
        assert result is not None
        assert "site_name" in result
        assert "test" in result

    def test_extract_json_without_code_block(self):
        llm = LLMEngine()
        text = '{"site_name": "direct", "base_url": "https://direct.com"}'
        result = llm._extract_json(text)
        assert result is not None
        assert "direct" in result

    def test_extract_json_no_json(self):
        llm = LLMEngine()
        text = "This is just plain text without any JSON"
        result = llm._extract_json(text)
        assert result is None

    def test_fallback_strategy_mangadex(self):
        llm = LLMEngine()
        strategy = llm._get_fallback_strategy("https://mangadex.org/title/abc123")
        assert strategy.site_name == "MangaDex"
        assert strategy.has_api is True
        assert strategy.api_endpoint == "https://api.mangadex.org"

    def test_fallback_strategy_mangapark(self):
        llm = LLMEngine()
        strategy = llm._get_fallback_strategy("https://mangapark.net/title/xyz")
        assert strategy.site_name == "mangapark.net"
        assert strategy.uses_javascript is True

    def test_fallback_strategy_unknown(self):
        llm = LLMEngine()
        strategy = llm._get_fallback_strategy("https://unknown-site.com/title/test")
        assert strategy.site_name == "unknown-site.com"
        assert strategy.uses_javascript is True


class TestDownloadManager:
    def test_extract_chapter_id_mangadex(self):
        from app.services.downloader import DownloadManager
        dm = DownloadManager()

        chapter_id = dm._extract_chapter_id("https://api.mangadex.org/chapter/abc-123-def")
        assert chapter_id == "abc-123-def"

        chapter_id = dm._extract_chapter_id("https://mangadex.org/chapter/xyz-789")
        assert chapter_id == "xyz-789"

        chapter_id = dm._extract_chapter_id("https://not-mangadex.com/chapter/123")
        assert chapter_id is None


class TestURLValidation:
    """Test SSRF prevention in library router"""

    def test_private_ip_patterns_blocked(self):
        import re
        from app.routers.library import PRIVATE_IP_RE

        # These should all match (be blocked)
        assert PRIVATE_IP_RE.match("127.0.0.1")
        assert PRIVATE_IP_RE.match("127.0.0.2")
        assert PRIVATE_IP_RE.match("10.0.0.1")
        assert PRIVATE_IP_RE.match("10.255.255.255")
        assert PRIVATE_IP_RE.match("172.16.0.1")
        assert PRIVATE_IP_RE.match("172.31.255.255")
        assert PRIVATE_IP_RE.match("192.168.0.1")
        assert PRIVATE_IP_RE.match("192.168.255.255")
        assert PRIVATE_IP_RE.match("169.254.0.1")
        assert PRIVATE_IP_RE.match("169.254.255.254")

    def test_public_ip_not_blocked(self):
        import re
        from app.routers.library import PRIVATE_IP_RE

        # These should NOT match (allowed)
        assert not PRIVATE_IP_RE.match("8.8.8.8")
        assert not PRIVATE_IP_RE.match("1.1.1.1")
        assert not PRIVATE_IP_RE.match("54.239.28.85")  # AWS
        assert not PRIVATE_IP_RE.match("151.101.1.140")  # Reddit

    def test_validate_url_rejects_private(self):
        from app.routers.library import validate_url
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            validate_url("http://127.0.0.1:8080")
        assert "Private IP" in str(exc_info.value.detail)

        with pytest.raises(HTTPException) as exc_info:
            validate_url("http://192.168.1.1/internal")
        assert "Private IP" in str(exc_info.value.detail)

    def test_validate_url_rejects_cloud_metadata(self):
        from app.routers.library import validate_url
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            validate_url("http://169.254.169.254/latest/meta-data")
        assert "Cloud metadata" in str(exc_info.value.detail)

    def test_validate_url_rejects_ftp(self):
        from app.routers.library import validate_url
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            validate_url("ftp://files.server.com")
        assert "Only HTTP/HTTPS" in str(exc_info.value.detail)

    def test_validate_url_rejects_credentials(self):
        from app.routers.library import validate_url
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            validate_url("http://user:pass@evil.com")
        assert "credentials" in str(exc_info.value.detail)

    def test_validate_url_accepts_https(self):
        from app.routers.library import validate_url

        # Should not raise
        result = validate_url("https://mangadex.org/title/abc")
        assert result == "https://mangadex.org/title/abc"