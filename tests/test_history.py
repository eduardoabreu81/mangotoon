from fastapi.testclient import TestClient

from app.main import app
from app.services import storage


COMIC_ID = "history-comic"
CHAPTER_ID = "chapter-001"


def setup_history_storage(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path)
    monkeypatch.setattr(storage, "COMICS_DIR", tmp_path / "comics")
    storage.save_history({"version": 1, "items": []})


def setup_history_comic(tmp_path, monkeypatch) -> None:
    setup_history_storage(tmp_path, monkeypatch)
    comic = {
        "comic_id": COMIC_ID,
        "title": "History Test Manga",
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
                "title": "Chapter One",
                "chapter_number": "1",
                "volume": "1",
                "language": "en",
                "pages": 12,
                "status": "downloaded",
                "downloaded_pages": 12,
                "error_message": "",
            }
        ],
    }
    storage.save_library({"version": 1, "comics": [comic]})
    storage.save_comic_metadata(COMIC_ID, comic)


def test_get_history_returns_empty_list_initially(tmp_path, monkeypatch):
    setup_history_storage(tmp_path, monkeypatch)

    response = TestClient(app).get("/api/history")

    assert response.status_code == 200
    assert response.json() == {"items": []}


def test_get_history_returns_items_after_progress_save(tmp_path, monkeypatch):
    setup_history_comic(tmp_path, monkeypatch)
    client = TestClient(app)

    progress_response = client.post(
        f"/api/reader/{COMIC_ID}/progress",
        json={"chapter_id": CHAPTER_ID, "page": 7, "total_pages": 12},
    )
    history_response = client.get("/api/history")

    assert progress_response.status_code == 200
    assert history_response.status_code == 200
    data = history_response.json()
    assert "items" in data
    items = data["items"]
    assert len(items) == 1
    assert items[0]["comic_id"] == COMIC_ID
    assert items[0]["title"] == "History Test Manga"
    assert items[0]["chapter_id"] == CHAPTER_ID
    assert items[0]["chapter_number"] == "1"
    assert items[0]["page_number"] == 7
    assert "last_read_at" in items[0]


def test_delete_history_item_removes_item(tmp_path, monkeypatch):
    setup_history_comic(tmp_path, monkeypatch)
    client = TestClient(app)
    client.post(
        f"/api/reader/{COMIC_ID}/progress",
        json={"chapter_id": CHAPTER_ID, "page": 7, "total_pages": 12},
    )

    delete_response = client.delete(f"/api/history/{COMIC_ID}")
    history_response = client.get("/api/history")

    assert delete_response.status_code == 200
    assert delete_response.json() == {"message": "History item deleted.", "comic_id": COMIC_ID}
    assert history_response.json() == {"items": []}


def test_delete_history_item_returns_404_for_missing_comic(tmp_path, monkeypatch):
    setup_history_storage(tmp_path, monkeypatch)

    response = TestClient(app).delete("/api/history/missing-comic")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
