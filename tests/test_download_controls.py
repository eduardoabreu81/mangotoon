import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import download_manager as download_manager_module
from app.services import storage
from app.services.download_manager import DownloadJob


COMIC_ID = "control-comic"
CHAPTER_ID = "chapter-001"


def sample_comic(chapter_status: str = "not_downloaded") -> dict:
    return {
        "comic_id": COMIC_ID,
        "title": "Control Test",
        "source": "MangaDex",
        "source_url": "https://mangadex.org/title/391b0423-d847-456f-aff0-8b0cfc03066b",
        "source_id": "391b0423-d847-456f-aff0-8b0cfc03066b",
        "description": "",
        "cover_url": "",
        "cover_local": "",
        "status": "pending",
        "chapters": [
            {
                "chapter_id": CHAPTER_ID,
                "title": "Chapter One",
                "chapter_number": "1",
                "volume": "",
                "language": "en",
                "pages": 0,
                "status": chapter_status,
                "downloaded_pages": 0,
                "error_message": "",
            }
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
def reset_download_manager():
    manager = download_manager_module.download_manager
    manager._jobs.clear()
    while not manager._queue.empty():
        manager._queue.get_nowait()
        manager._queue.task_done()
    yield
    manager._jobs.clear()
    while not manager._queue.empty():
        manager._queue.get_nowait()
        manager._queue.task_done()


def add_active_job(status: str = "queued") -> None:
    job = DownloadJob(COMIC_ID, total_chapters=1)
    job.status = status
    download_manager_module.download_manager._jobs[COMIC_ID] = job


def test_pause_download_endpoint(isolated_storage):
    add_active_job("queued")

    response = TestClient(app).post(f"/api/downloads/{COMIC_ID}/pause")

    assert response.status_code == 200
    assert response.json()["state"] == "paused"
    assert download_manager_module.download_manager.get_status(COMIC_ID)["state"] == "paused"
    assert storage.load_comic_metadata(COMIC_ID)["status"] == "paused"


def test_resume_download_endpoint(isolated_storage):
    add_active_job("paused")

    response = TestClient(app).post(f"/api/downloads/{COMIC_ID}/resume")

    assert response.status_code == 200
    assert response.json()["state"] == "queued"
    assert download_manager_module.download_manager.get_status(COMIC_ID)["state"] == "queued"


def test_cancel_download_endpoint_clears_queued_items(isolated_storage):
    add_active_job("queued")
    download_manager_module.download_manager._queue.put_nowait((COMIC_ID, {"chapter_id": CHAPTER_ID}))

    response = TestClient(app).post(f"/api/downloads/{COMIC_ID}/cancel")

    assert response.status_code == 200
    assert response.json()["state"] == "cancelled"
    assert download_manager_module.download_manager._queue.empty()
    assert storage.load_comic_metadata(COMIC_ID)["status"] == "cancelled"


def test_retry_chapter_endpoint_queues_failed_chapter(isolated_storage):
    comic = sample_comic(chapter_status="error")
    storage.save_library({"version": 1, "comics": [comic]})
    storage.save_comic_metadata(COMIC_ID, comic)

    response = TestClient(app).post(f"/api/downloads/{COMIC_ID}/chapters/{CHAPTER_ID}/retry")

    assert response.status_code == 200
    assert response.json()["state"] == "queued"
    assert download_manager_module.download_manager.get_status(COMIC_ID)["state"] == "queued"
    chapter = storage.load_comic_metadata(COMIC_ID)["chapters"][0]
    assert chapter["status"] == "queued"
    assert not download_manager_module.download_manager._queue.empty()


def test_retry_chapter_returns_404_for_non_failed_chapter(isolated_storage):
    response = TestClient(app).post(f"/api/downloads/{COMIC_ID}/chapters/{CHAPTER_ID}/retry")

    assert response.status_code == 404


def test_download_status_includes_state(isolated_storage):
    add_active_job("running")

    response = TestClient(app).get(f"/api/downloads/{COMIC_ID}/status")

    assert response.status_code == 200
    assert response.json()["status"] == "running"
    assert response.json()["state"] == "running"


def test_pause_returns_404_for_missing_download(isolated_storage):
    response = TestClient(app).post("/api/downloads/missing/pause")

    assert response.status_code == 404
