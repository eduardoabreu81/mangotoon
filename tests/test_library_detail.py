"""Tests for the manga detail backend endpoint."""

from fastapi.testclient import TestClient

from app.main import app
from app.services import storage


COMIC_ID = "detail-comic"


def sample_detail_comic() -> dict:
    return {
        "comic_id": COMIC_ID,
        "title": "Detail Test Manga",
        "source": "MangaDex",
        "source_url": "https://mangadex.org/title/detail-comic",
        "source_id": "detail-comic",
        "description": "Detail endpoint test fixture.",
        "cover_url": "https://example.test/cover.jpg",
        "cover_local": "comics/detail-comic/cover.jpg",
        "status": "partial",
        "reading_progress": {
            "chapter_id": "chapter-002",
            "page": 3,
            "total_pages": 20,
            "updated_at": "2026-05-17T00:00:00Z",
        },
        "completed_chapters": ["chapter-001"],
        "chapters": [
            {
                "chapter_id": "chapter-001",
                "title": "Chapter One",
                "chapter_number": "1",
                "volume": "1",
                "language": "en",
                "pages": 20,
                "status": "downloaded",
                "downloaded_pages": 20,
                "local_pages": ["comics/detail-comic/chapters/chapter-001/001.jpg"],
            },
            {
                "chapter_id": "chapter-002",
                "title": "Chapter Two",
                "chapter_number": "2",
                "volume": "1",
                "language": "en",
                "pages": 20,
                "status": "partial",
                "downloaded_pages": 3,
                "local_pages": ["comics/detail-comic/chapters/chapter-002/001.jpg"],
            },
        ],
    }


def setup_detail_storage(tmp_path, monkeypatch) -> dict:
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path)
    monkeypatch.setattr(storage, "COMICS_DIR", tmp_path / "comics")
    comic = sample_detail_comic()
    storage.save_library({"version": 1, "comics": [comic]})
    storage.save_comic_metadata(COMIC_ID, comic)
    return comic


def test_detail_endpoint_returns_200(tmp_path, monkeypatch):
    setup_detail_storage(tmp_path, monkeypatch)

    response = TestClient(app).get(f"/api/library/{COMIC_ID}/detail")

    assert response.status_code == 200
    data = response.json()
    assert data["comic_id"] == COMIC_ID
    assert data["title"] == "Detail Test Manga"
    assert data["cover_local"] == "comics/detail-comic/cover.jpg"
    assert data["reading_progress"]["chapter_id"] == "chapter-002"


def test_detail_endpoint_returns_404(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path)
    monkeypatch.setattr(storage, "COMICS_DIR", tmp_path / "comics")
    storage.save_library({"version": 1, "comics": []})

    response = TestClient(app).get("/api/library/missing-comic/detail")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_detail_includes_chapters_with_status(tmp_path, monkeypatch):
    setup_detail_storage(tmp_path, monkeypatch)

    response = TestClient(app).get(f"/api/library/{COMIC_ID}/detail")

    assert response.status_code == 200
    chapters = response.json()["chapters"]
    assert [chapter["status"] for chapter in chapters] == ["downloaded", "partial"]
    assert chapters[0]["completed"] is True
    assert chapters[1]["is_current"] is True
