import asyncio

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers import library as library_router
from app.services import download_manager as download_manager_module
from app.services import storage
from app.services.download_manager import DownloadManager


COMIC_ID = "mangadex-test"


def sample_comic() -> dict:
    return {
        "comic_id": COMIC_ID,
        "title": "Download Test",
        "source": "MangaDex",
        "source_url": "https://mangadex.org/title/391b0423-d847-456f-aff0-8b0cfc03066b",
        "source_id": "391b0423-d847-456f-aff0-8b0cfc03066b",
        "description": "",
        "cover_url": "",
        "cover_local": "",
        "status": "pending",
        "chapters": [
            {
                "chapter_id": "chapter-001",
                "title": "Chapter One",
                "chapter_number": "1",
                "volume": "",
                "language": "en",
                "pages": 0,
                "status": "not_downloaded",
                "downloaded_pages": 0,
                "error_message": "",
            },
            {
                "chapter_id": "chapter-002",
                "title": "Chapter Two",
                "chapter_number": "2",
                "volume": "",
                "language": "en",
                "pages": 0,
                "status": "not_downloaded",
                "downloaded_pages": 0,
                "error_message": "",
            },
        ],
    }


@pytest.fixture()
def isolated_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path)
    monkeypatch.setattr(storage, "COMICS_DIR", tmp_path / "comics")
    monkeypatch.setattr(download_manager_module, "COMICS_DIR", tmp_path / "comics")
    storage.save_library({"version": 1, "comics": [sample_comic()]})
    storage.save_comic_metadata(COMIC_ID, sample_comic())
    return tmp_path


@pytest.fixture(autouse=True)
def reset_global_download_manager():
    download_manager_module.download_manager._jobs.clear()
    while not download_manager_module.download_manager._queue.empty():
        download_manager_module.download_manager._queue.get_nowait()
        download_manager_module.download_manager._queue.task_done()
    yield
    download_manager_module.download_manager._jobs.clear()


@pytest.mark.asyncio
async def test_enqueue_comic_creates_job(isolated_storage, monkeypatch):
    manager = DownloadManager()

    async def fake_download_cover(comic_id, metadata):
        return None

    monkeypatch.setattr(manager, "_download_cover", fake_download_cover)

    await manager.enqueue_comic(COMIC_ID)

    status = manager.get_status(COMIC_ID)
    assert status is not None
    assert status["status"] in {"queued", "downloading"}
    assert status["total_chapters"] == 2


def test_get_status_falls_back_to_metadata(isolated_storage):
    meta = storage.load_comic_metadata(COMIC_ID)
    meta["chapters"][0]["status"] = "downloaded"
    meta["chapters"][1]["status"] = "error"
    storage.save_comic_metadata(COMIC_ID, meta)

    response = TestClient(app).get(f"/api/downloads/{COMIC_ID}/status")

    assert response.status_code == 200
    data = response.json()
    assert data["comic_id"] == COMIC_ID
    assert data["status"] == "partial"
    assert data["downloaded_chapters"] == 1
    assert data["error_chapters"] == 1


def test_get_status_returns_404_for_unknown_comic(isolated_storage):
    response = TestClient(app).get("/api/downloads/notfound/status")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_download_endpoint_returns_200(isolated_storage, monkeypatch):
    called = asyncio.Event()

    async def fake_enqueue_comic(comic_id):
        called.set()

    monkeypatch.setattr(library_router.download_manager, "enqueue_comic", fake_enqueue_comic)

    response = TestClient(app).post(f"/api/library/{COMIC_ID}/download")

    assert response.status_code == 200
    assert response.json() == {"message": "Download started.", "comic_id": COMIC_ID}


def test_download_endpoint_404_for_missing(isolated_storage):
    response = TestClient(app).post("/api/library/notfound/download")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_chapter_download_endpoint_200(isolated_storage, monkeypatch):
    async def fake_enqueue_chapter(comic_id, chapter_id):
        return None

    monkeypatch.setattr(library_router.download_manager, "enqueue_chapter", fake_enqueue_chapter)

    response = TestClient(app).post(f"/api/library/{COMIC_ID}/chapters/chapter-001/download")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Chapter download started.",
        "comic_id": COMIC_ID,
        "chapter_id": "chapter-001",
    }


def test_list_active_downloads(isolated_storage):
    response = TestClient(app).get("/api/downloads")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_chapter_status_persisted_after_download(isolated_storage):
    manager = DownloadManager()

    manager._persist_chapter_downloaded(COMIC_ID, "chapter-001", total_pages=3, downloaded_pages=3, local_pages=["comics/mangadex-test/chapters/chapter-001/001.jpg"], failed=False)

    meta = storage.load_comic_metadata(COMIC_ID)
    chapter = next(ch for ch in meta["chapters"] if ch["chapter_id"] == "chapter-001")
    assert chapter["status"] == "downloaded"
    assert chapter["pages"] == 3
    assert chapter["downloaded_pages"] == 3
    assert chapter["local_pages"] == ["comics/mangadex-test/chapters/chapter-001/001.jpg"]


def test_partial_download_marks_chapter_error(isolated_storage):
    manager = DownloadManager()

    manager._persist_chapter_downloaded(COMIC_ID, "chapter-001", total_pages=3, downloaded_pages=0, local_pages=[], failed=True)

    meta = storage.load_comic_metadata(COMIC_ID)
    chapter = next(ch for ch in meta["chapters"] if ch["chapter_id"] == "chapter-001")
    assert chapter["status"] == "error"
    assert chapter["downloaded_pages"] == 0


def test_partial_download_marks_chapter_partial(isolated_storage):
    manager = DownloadManager()

    manager._persist_chapter_downloaded(COMIC_ID, "chapter-001", total_pages=3, downloaded_pages=1, local_pages=["comics/mangadex-test/chapters/chapter-001/001.jpg"], failed=True)

    meta = storage.load_comic_metadata(COMIC_ID)
    chapter = next(ch for ch in meta["chapters"] if ch["chapter_id"] == "chapter-001")
    assert chapter["status"] == "partial"
    assert chapter["downloaded_pages"] == 1
    assert chapter["local_pages"] == ["comics/mangadex-test/chapters/chapter-001/001.jpg"]


def test_library_response_validates_through_comic_model(isolated_storage):
    manager = DownloadManager()
    manager._persist_chapter_downloaded(COMIC_ID, "chapter-001", total_pages=3, downloaded_pages=3, local_pages=["a.jpg"], failed=False)

    response = TestClient(app).get("/api/library")
    assert response.status_code == 200
    data = response.json()
    assert "comics" in data
    comic = data["comics"][0]
    # Should validate through Comic Pydantic model
    assert "chapter_count" in comic
    assert "downloaded_count" in comic
    assert comic["chapter_count"] == 2
    assert comic["downloaded_count"] == 1


@pytest.mark.asyncio
async def test_fetch_with_retry_uses_mocked_httpx(monkeypatch):
    async_client_class = httpx.AsyncClient

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"page-bytes", request=request)

    def make_client(*args, **kwargs):
        return async_client_class(transport=httpx.MockTransport(handler))

    monkeypatch.setattr(download_manager_module.httpx, "AsyncClient", make_client)

    manager = DownloadManager()
    manager._rate_limit = 0
    content = await manager._fetch_with_retry("https://pages.example/001.jpg")

    assert content == b"page-bytes"
