from fastapi.testclient import TestClient

from app.main import app
from app.services import storage


COMIC_ID = "reader-comic"
CHAPTER_ID = "chapter-001"


def make_comic(downloaded: bool = True) -> dict:
    first_status = "downloaded" if downloaded else "not_downloaded"
    return {
        "comic_id": COMIC_ID,
        "title": "Reader Test Manga",
        "source": "MangaDex",
        "source_url": "https://mangadex.org/title/391b0423-d847-456f-aff0-8b0cfc03066b",
        "source_id": "391b0423-d847-456f-aff0-8b0cfc03066b",
        "description": "",
        "cover_url": "",
        "cover_local": "",
        "status": "partial",
        "chapters": [
            {
                "chapter_id": CHAPTER_ID,
                "title": "Downloaded Chapter",
                "chapter_number": "1",
                "volume": "1",
                "language": "en",
                "pages": 1,
                "status": first_status,
                "downloaded_pages": 1 if downloaded else 0,
                "error_message": "",
            },
            {
                "chapter_id": "chapter-002",
                "title": "Missing Chapter",
                "chapter_number": "2",
                "volume": "1",
                "language": "en",
                "pages": 0,
                "status": "not_downloaded",
                "downloaded_pages": 0,
                "error_message": "",
            },
        ],
    }


def setup_reader_comic(tmp_path, monkeypatch, downloaded: bool = True) -> dict:
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path)
    monkeypatch.setattr(storage, "COMICS_DIR", tmp_path / "comics")

    comic = make_comic(downloaded=downloaded)
    storage.save_library({"version": 1, "comics": [comic]})
    storage.save_comic_metadata(COMIC_ID, comic)
    storage.save_history({"version": 1, "items": []})

    chapter_dir = tmp_path / "comics" / COMIC_ID / "chapters" / CHAPTER_ID
    chapter_dir.mkdir(parents=True, exist_ok=True)
    if downloaded:
        (chapter_dir / "001.jpg").write_bytes(b"fake-image-data")
    return comic


def test_reader_data_returns_downloaded_chapters(tmp_path, monkeypatch):
    setup_reader_comic(tmp_path, monkeypatch)

    response = TestClient(app).get(f"/api/reader/{COMIC_ID}/data")

    assert response.status_code == 200
    data = response.json()
    assert data["comic_id"] == COMIC_ID
    assert data["title"] == "Reader Test Manga"
    assert len(data["chapters"]) == 1
    assert data["chapters"][0]["chapter_id"] == CHAPTER_ID
    assert data["chapters"][0]["pages"] == 1


def test_reader_data_returns_404_for_missing_comic(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path)
    monkeypatch.setattr(storage, "COMICS_DIR", tmp_path / "comics")

    response = TestClient(app).get("/api/reader/nonexistent/data")

    assert response.status_code == 404


def test_reader_data_returns_empty_chapters_when_nothing_downloaded(tmp_path, monkeypatch):
    setup_reader_comic(tmp_path, monkeypatch, downloaded=False)

    response = TestClient(app).get(f"/api/reader/{COMIC_ID}/data")

    assert response.status_code == 200
    assert response.json()["chapters"] == []


def test_page_endpoint_serves_image(tmp_path, monkeypatch):
    setup_reader_comic(tmp_path, monkeypatch)

    response = TestClient(app).get(f"/api/reader/{COMIC_ID}/{CHAPTER_ID}/1")

    assert response.status_code == 200
    assert response.content == b"fake-image-data"


def test_page_endpoint_returns_404_for_missing_page(tmp_path, monkeypatch):
    setup_reader_comic(tmp_path, monkeypatch)

    response = TestClient(app).get(f"/api/reader/{COMIC_ID}/{CHAPTER_ID}/99")

    assert response.status_code == 404
    assert response.json()["detail"] == "Page not found"


def test_page_endpoint_rejects_path_traversal(tmp_path, monkeypatch):
    setup_reader_comic(tmp_path, monkeypatch)

    comic_response = TestClient(app).get(f"/api/reader/../etc/{CHAPTER_ID}/1")
    assert comic_response.status_code in {400, 404, 422}

    chapter_response = TestClient(app).get(f"/api/reader/{COMIC_ID}/%2E%2E/1")
    assert chapter_response.status_code == 400
    assert chapter_response.json()["detail"] == "Invalid comic or chapter ID"


def test_progress_save_and_load(tmp_path, monkeypatch):
    setup_reader_comic(tmp_path, monkeypatch)
    client = TestClient(app)

    save_response = client.post(
        f"/api/reader/{COMIC_ID}/progress",
        json={"chapter_id": CHAPTER_ID, "page": 5, "total_pages": 24},
    )
    load_response = client.get(f"/api/reader/{COMIC_ID}/progress")

    assert save_response.status_code == 200
    assert save_response.json()["ok"] is True
    assert load_response.status_code == 200
    assert load_response.json()["chapter_id"] == CHAPTER_ID
    assert load_response.json()["page"] == 5
    assert load_response.json()["total_pages"] == 24


def test_progress_updates_history(tmp_path, monkeypatch):
    setup_reader_comic(tmp_path, monkeypatch)

    response = TestClient(app).post(
        f"/api/reader/{COMIC_ID}/progress",
        json={"chapter_id": CHAPTER_ID, "page": 3, "total_pages": 24},
    )

    assert response.status_code == 200
    history = storage.load_history()
    assert len(history["items"]) == 1
    assert history["items"][0]["comic_id"] == COMIC_ID
    assert history["items"][0]["chapter_id"] == CHAPTER_ID
    assert history["items"][0]["page_number"] == 3


def test_progress_marks_completed_chapter(tmp_path, monkeypatch):
    setup_reader_comic(tmp_path, monkeypatch)

    response = TestClient(app).post(
        f"/api/reader/{COMIC_ID}/progress",
        json={"chapter_id": CHAPTER_ID, "page": 24, "total_pages": 24, "completed": True},
    )

    assert response.status_code == 200
    meta = storage.load_comic_metadata(COMIC_ID)
    assert CHAPTER_ID in meta["completed_chapters"]
