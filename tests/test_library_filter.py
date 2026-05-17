from fastapi.testclient import TestClient

from app.main import app
from app.services import storage


def make_comic(
    comic_id: str,
    title: str,
    status: str,
    source: str = "MangaDex",
    downloaded_chapters: int = 0,
) -> dict:
    chapters = []
    for index in range(2):
        chapter_status = "downloaded" if index < downloaded_chapters else "not_downloaded"
        chapters.append(
            {
                "chapter_id": f"{comic_id}-chapter-{index + 1}",
                "title": f"Chapter {index + 1}",
                "chapter_number": str(index + 1),
                "volume": "",
                "language": "en",
                "pages": 10,
                "status": chapter_status,
                "downloaded_pages": 10 if chapter_status == "downloaded" else 0,
                "error_message": "",
            }
        )
    return {
        "comic_id": comic_id,
        "title": title,
        "source": source,
        "source_url": f"https://example.test/{comic_id}",
        "source_id": comic_id,
        "description": "",
        "cover_url": "",
        "cover_local": "",
        "status": status,
        "chapters": chapters,
        "created_at": f"2026-01-0{len(title) % 9 + 1}T00:00:00",
        "updated_at": f"2026-02-0{len(title) % 9 + 1}T00:00:00",
    }


def setup_library(tmp_path, monkeypatch) -> list[dict]:
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path)
    monkeypatch.setattr(storage, "COMICS_DIR", tmp_path / "comics")
    comics = [
        make_comic("comic-reading", "Beta", "reading", downloaded_chapters=1),
        make_comic("comic-completed", "Alpha", "completed", downloaded_chapters=2),
        make_comic("comic-pending", "Gamma", "pending", source="Local", downloaded_chapters=0),
    ]
    storage.save_library({"version": 1, "comics": comics})
    for comic in comics:
        storage.save_comic_metadata(comic["comic_id"], comic)
    return comics


def test_filter_library_by_status(tmp_path, monkeypatch):
    setup_library(tmp_path, monkeypatch)

    response = TestClient(app).get("/api/library/filter?status=reading")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["comics"][0]["comic_id"] == "comic-reading"


def test_filter_library_by_downloaded_status(tmp_path, monkeypatch):
    setup_library(tmp_path, monkeypatch)

    response = TestClient(app).get("/api/library/filter?status=downloaded")

    assert response.status_code == 200
    ids = {comic["comic_id"] for comic in response.json()["comics"]}
    assert ids == {"comic-reading", "comic-completed"}


def test_filter_library_by_source_and_sort_title(tmp_path, monkeypatch):
    setup_library(tmp_path, monkeypatch)

    response = TestClient(app).get("/api/library/filter?source=MangaDex&sort=title")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert [comic["title"] for comic in data["comics"]] == ["Alpha", "Beta"]


def test_update_comic_status_persists_to_library_and_metadata(tmp_path, monkeypatch):
    setup_library(tmp_path, monkeypatch)

    response = TestClient(app).post("/api/library/comic-pending/status", json={"status": "reading"})

    assert response.status_code == 200
    assert response.json()["status"] == "reading"
    assert storage.load_comic_metadata("comic-pending")["status"] == "reading"
    library_comic = next(comic for comic in storage.load_library()["comics"] if comic["comic_id"] == "comic-pending")
    assert library_comic["status"] == "reading"


def test_update_comic_status_rejects_invalid_status(tmp_path, monkeypatch):
    setup_library(tmp_path, monkeypatch)

    response = TestClient(app).post("/api/library/comic-pending/status", json={"status": "archived"})

    assert response.status_code == 422


def test_update_comic_status_returns_404_for_missing_comic(tmp_path, monkeypatch):
    setup_library(tmp_path, monkeypatch)

    response = TestClient(app).post("/api/library/missing/status", json={"status": "reading"})

    assert response.status_code == 404
