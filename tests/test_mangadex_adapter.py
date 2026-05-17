import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers import library as library_router
from app.services.source_registry import SourceRegistry
from app.services import storage
from app.sources.base import SourceNotFound
from app.sources.mangadex import MangaDexAdapter


TITLE_ID = "391b0423-d847-456f-aff0-8b0cfc03066b"


def mangadex_title_payload() -> dict:
    return {
        "result": "ok",
        "data": {
            "id": TITLE_ID,
            "type": "manga",
            "attributes": {
                "title": {"en": "Test Manga"},
                "description": {"en": "A MangaDex metadata fixture."},
            },
            "relationships": [
                {
                    "id": "cover-001",
                    "type": "cover_art",
                    "attributes": {"fileName": "cover-file.jpg"},
                }
            ],
        },
    }


def mangadex_feed_payload() -> dict:
    return {
        "result": "ok",
        "data": [
            {
                "id": "chapter-001",
                "type": "chapter",
                "attributes": {
                    "title": "Chapter One",
                    "chapter": "1",
                    "volume": "1",
                    "translatedLanguage": "en",
                    "pages": 24,
                },
            },
            {
                "id": "chapter-002",
                "type": "chapter",
                "attributes": {
                    "title": "Chapter Two",
                    "chapter": "2",
                    "volume": "1",
                    "translatedLanguage": "en",
                    "pages": 18,
                },
            },
        ],
        "limit": 100,
        "offset": 0,
        "total": 2,
    }


def make_transport(status_code: int = 200, calls: list[str] | None = None) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        if calls is not None:
            calls.append(request.url.path)

        if status_code != 200:
            return httpx.Response(status_code, json={"result": "error"}, request=request)
        if request.url.path == f"/manga/{TITLE_ID}":
            return httpx.Response(200, json=mangadex_title_payload(), request=request)
        if request.url.path == f"/manga/{TITLE_ID}/feed":
            return httpx.Response(200, json=mangadex_feed_payload(), request=request)
        return httpx.Response(404, json={"result": "error"}, request=request)

    return httpx.MockTransport(handler)


@pytest.fixture()
def isolated_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path)
    monkeypatch.setattr(storage, "COMICS_DIR", tmp_path / "comics")
    storage.save_library({"version": 1, "comics": []})
    return tmp_path


def test_mangadex_url_detection_and_title_id_extraction():
    adapter = MangaDexAdapter()

    assert adapter.can_handle(f"https://mangadex.org/title/{TITLE_ID}/test-manga")
    assert adapter.can_handle(f"https://www.mangadex.org/title/{TITLE_ID}")
    assert adapter.get_source_id(f"https://mangadex.org/title/{TITLE_ID}/test-manga") == TITLE_ID
    assert not adapter.can_handle("https://example.com/title/not-supported")


@pytest.mark.asyncio
async def test_mangadex_adapter_normalizes_metadata():
    async with httpx.AsyncClient(transport=make_transport(), base_url="https://api.mangadex.org") as client:
        adapter = MangaDexAdapter(client=client)
        comic = await adapter.fetch_comic(f"https://mangadex.org/title/{TITLE_ID}/test-manga")

    assert comic.comic_id == f"mangadex-{TITLE_ID}"
    assert comic.title == "Test Manga"
    assert comic.source == "MangaDex"
    assert comic.source_id == TITLE_ID
    assert comic.cover_url == f"https://uploads.mangadex.org/covers/{TITLE_ID}/cover-file.jpg.256.jpg"
    assert comic.chapter_count == 2
    assert comic.chapters[0].chapter_id == "chapter-001"
    assert comic.chapters[0].chapter_number == "1"
    assert comic.chapters[0].pages == 24


@pytest.mark.asyncio
async def test_mangadex_adapter_raises_not_found_for_missing_title():
    async with httpx.AsyncClient(transport=make_transport(status_code=404), base_url="https://api.mangadex.org") as client:
        adapter = MangaDexAdapter(client=client)
        with pytest.raises(SourceNotFound):
            await adapter.fetch_comic(f"https://mangadex.org/title/{TITLE_ID}/missing")


def test_add_mangadex_comic_endpoint_saves_library_and_metadata(isolated_storage, monkeypatch):
    async_client = httpx.AsyncClient(transport=make_transport(), base_url="https://api.mangadex.org")
    monkeypatch.setattr(library_router, "source_registry", SourceRegistry([MangaDexAdapter(client=async_client)]))

    try:
        response = TestClient(app).post("/api/library/add", json={"url": f"https://mangadex.org/title/{TITLE_ID}/test-manga"})
    finally:
        import asyncio

        asyncio.run(async_client.aclose())

    assert response.status_code == 200
    data = response.json()
    assert data["duplicate"] is False
    assert data["comic"]["title"] == "Test Manga"
    assert data["comic"]["chapter_count"] == 2

    library = storage.load_library()
    assert len(library["comics"]) == 1
    assert library["comics"][0]["source_id"] == TITLE_ID

    metadata_path = isolated_storage / "comics" / f"mangadex-{TITLE_ID}" / "metadata.json"
    assert metadata_path.exists()


def test_add_mangadex_comic_endpoint_prevents_duplicates(isolated_storage, monkeypatch):
    calls: list[str] = []
    async_client = httpx.AsyncClient(transport=make_transport(calls=calls), base_url="https://api.mangadex.org")
    monkeypatch.setattr(library_router, "source_registry", SourceRegistry([MangaDexAdapter(client=async_client)]))
    client = TestClient(app)

    try:
        first = client.post("/api/library/add", json={"url": f"https://mangadex.org/title/{TITLE_ID}/test-manga"})
        second = client.post("/api/library/add", json={"url": f"https://mangadex.org/title/{TITLE_ID}"})
    finally:
        import asyncio

        asyncio.run(async_client.aclose())

    assert first.status_code == 200
    assert first.json()["duplicate"] is False
    assert second.status_code == 200
    assert second.json()["duplicate"] is True
    assert len(storage.load_library()["comics"]) == 1
    assert calls.count(f"/manga/{TITLE_ID}") == 1


def test_add_mangadex_comic_endpoint_rejects_unsupported_source(isolated_storage):
    response = TestClient(app).post("/api/library/add", json={"url": "https://example.com/title/test"})

    assert response.status_code == 400
    assert "unsupported" in response.json()["detail"].lower()
