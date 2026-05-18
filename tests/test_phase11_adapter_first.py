from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.comic import Chapter, Comic
from app.services import download_manager as download_manager_module
from app.services import storage
from app.services.download_manager import DownloadManager
from app.services.source_registry import SourceRegistry
from app.sources.fake import FakeSourceAdapter
from app.sources.mangadex import MangaDexAdapter


FAKE_COMIC_ID = "fake-phase11"
FAKE_CHAPTER_ID = "chapter-001"


def fake_comic() -> dict:
    return {
        "comic_id": FAKE_COMIC_ID,
        "title": "Phase 11 Fake",
        "source": "Fake",
        "source_url": "fake://phase11",
        "source_id": "phase11",
        "description": "",
        "cover_url": "",
        "cover_local": "",
        "status": "pending",
        "chapters": [
            {
                "chapter_id": FAKE_CHAPTER_ID,
                "source_chapter_id": "fake-source-chapter-001",
                "title": "Chapter One",
                "chapter_number": "1",
                "volume": "",
                "language": "en",
                "pages": 0,
                "status": "not_downloaded",
                "downloaded_pages": 0,
                "local_pages": [],
                "error_message": "",
            }
        ],
    }


@pytest.fixture()
def isolated_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path)
    monkeypatch.setattr(storage, "COMICS_DIR", tmp_path / "comics")
    monkeypatch.setattr(download_manager_module, "COMICS_DIR", tmp_path / "comics")
    storage.save_library({"version": 1, "comics": [fake_comic()]})
    storage.save_comic_metadata(FAKE_COMIC_ID, fake_comic())
    storage.save_history({"version": 1, "items": []})
    return tmp_path


@pytest.mark.asyncio
async def test_download_manager_uses_registry_not_mangadex(isolated_storage, monkeypatch):
    adapter = FakeSourceAdapter(pages=["https://fake.local/001.jpg", "https://fake.local/002.png"])
    monkeypatch.setattr(download_manager_module, "source_registry", SourceRegistry([adapter]))

    async def fake_fetch(url: str) -> bytes:
        return f"bytes:{url}".encode()

    manager = DownloadManager()
    monkeypatch.setattr(manager, "_fetch_with_retry", fake_fetch)

    await manager._download_chapter(FAKE_COMIC_ID, fake_comic()["chapters"][0])

    meta = storage.load_comic_metadata(FAKE_COMIC_ID)
    chapter = meta["chapters"][0]
    assert chapter["status"] == "downloaded"
    assert chapter["pages"] == 2
    assert chapter["local_pages"] == [
        f"comics/{FAKE_COMIC_ID}/chapters/{FAKE_CHAPTER_ID}/001.jpg",
        f"comics/{FAKE_COMIC_ID}/chapters/{FAKE_CHAPTER_ID}/002.png",
    ]


@pytest.mark.asyncio
async def test_fake_adapter_provides_pages():
    adapter = FakeSourceAdapter(pages=["https://fake.local/page-1.jpg"])
    comic = await adapter.fetch_comic("fake://phase11")
    pages = await adapter.get_chapter_pages(comic, comic.chapters[0])

    assert comic.source == "Fake"
    assert comic.chapters[0].source_chapter_id == "fake-chapter-001"
    assert pages == ["https://fake.local/page-1.jpg"]


def test_reader_uses_local_pages(isolated_storage):
    old_dir = isolated_storage / "comics" / FAKE_COMIC_ID / "chapters" / FAKE_CHAPTER_ID
    old_dir.mkdir(parents=True)
    (old_dir / "001.jpg").write_bytes(b"old-glob-page")

    local_dir = isolated_storage / "comics" / FAKE_COMIC_ID / "stored-pages"
    local_dir.mkdir(parents=True)
    (local_dir / "preferred.jpg").write_bytes(b"preferred-local-page")

    meta = storage.load_comic_metadata(FAKE_COMIC_ID)
    meta["chapters"][0]["status"] = "downloaded"
    meta["chapters"][0]["pages"] = 1
    meta["chapters"][0]["downloaded_pages"] = 1
    meta["chapters"][0]["local_pages"] = [f"comics/{FAKE_COMIC_ID}/stored-pages/preferred.jpg"]
    storage.save_comic_metadata(FAKE_COMIC_ID, meta)

    client = TestClient(app)
    data_response = client.get(f"/api/reader/{FAKE_COMIC_ID}/data")
    page_response = client.get(f"/api/reader/{FAKE_COMIC_ID}/{FAKE_CHAPTER_ID}/1")

    assert data_response.status_code == 200
    assert data_response.json()["chapters"][0]["pages"] == 1
    assert page_response.status_code == 200
    # Phase 17.8 v3: get_page_image now uses metadata local_pages as fast path.
    # When local_pages is available, it resolves directly without dir scan.
    assert page_response.content == b"preferred-local-page"


@pytest.mark.asyncio
async def test_mangadex_still_works():
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        return httpx.Response(
            200,
            json={
                "baseUrl": "https://uploads.example",
                "chapter": {"hash": "hash-001", "data": ["001.jpg", "002.png"]},
            },
            request=request,
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://api.mangadex.org") as client:
        adapter = MangaDexAdapter(client=client)
        comic = Comic(
            comic_id="mangadex-title-001",
            title="MangaDex Test",
            source="MangaDex",
            source_url="https://mangadex.org/title/391b0423-d847-456f-aff0-8b0cfc03066b",
            source_id="391b0423-d847-456f-aff0-8b0cfc03066b",
        )
        chapter = Chapter(chapter_id="local-chapter-001", source_chapter_id="source-chapter-001")
        pages = await adapter.get_chapter_pages(comic, chapter)

    assert calls == ["/at-home/server/source-chapter-001"]
    assert pages == [
        "https://uploads.example/data/hash-001/001.jpg",
        "https://uploads.example/data/hash-001/002.png",
    ]


def test_no_core_imports_mangadex_directly():
    core_files = [
        Path("app/services/download_manager.py"),
        Path("app/routers/reader.py"),
    ]

    for path in core_files:
        source = path.read_text(encoding="utf-8")
        assert "from app.sources.mangadex import MangaDexAdapter" not in source
        assert "MangaDexAdapter()" not in source
