import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.models.comic import SourceCapabilities


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_list_sources_returns_capabilities(client):
    response = client.get("/api/sources")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    mangadex = next((s for s in data if s["name"] == "MangaDex"), None)
    assert mangadex is not None
    assert "domains" in mangadex
    assert "mangadex.org" in mangadex["domains"]
    assert "capabilities" in mangadex

    caps = mangadex["capabilities"]
    assert caps["metadata"] is True
    assert caps["cover"] is True
    assert caps["chapter_list"] is True
    assert caps["page_download"] is True
    assert caps["languages"] == ["en"]
    assert caps["supports_refresh"] is True
    assert caps["supports_search"] is False
    assert caps["requires_javascript"] is False
    assert caps["requires_auth"] is False


def test_detect_source_supported(client):
    response = client.post("/api/sources/detect", json={"url": "https://mangadex.org/title/12345678-1234-1234-1234-123456789abc"})
    assert response.status_code == 200
    data = response.json()
    assert data["supported"] is True
    assert data["source"] == "MangaDex"


def test_detect_source_unsupported(client):
    response = client.post("/api/sources/detect", json={"url": "https://example.com/manga/123"})
    assert response.status_code == 200
    data = response.json()
    assert data["supported"] is False
    assert data["source"] == ""


def test_source_capabilities_defaults():
    caps = SourceCapabilities()
    assert caps.metadata is True
    assert caps.cover is True
    assert caps.chapter_list is True
    assert caps.page_download is True
    assert caps.languages == []
    assert caps.supports_refresh is False
    assert caps.supports_search is False
    assert caps.requires_javascript is False
    assert caps.requires_auth is False


def test_source_capabilities_model_dump():
    caps = SourceCapabilities(
        metadata=True,
        cover=False,
        languages=["en", "pt-BR"],
        supports_refresh=True,
    )
    dumped = caps.model_dump()
    assert dumped["metadata"] is True
    assert dumped["cover"] is False
    assert dumped["languages"] == ["en", "pt-BR"]
    assert dumped["supports_refresh"] is True
