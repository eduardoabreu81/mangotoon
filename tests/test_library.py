"""Tests for library and settings endpoints."""

from fastapi.testclient import TestClient

from app.main import app
from app.services.storage import save_library, save_settings

client = TestClient(app)


class TestLibrary:
    def test_library_empty_on_fresh_install(self):
        response = client.get("/api/library")
        assert response.status_code == 200
        data = response.json()
        assert data["comics"] == []
        assert data["total"] == 0

    def test_get_comic_not_found(self):
        response = client.get("/api/library/nonexistent")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_comic_not_found(self):
        response = client.delete("/api/library/nonexistent")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_library_with_comic(self, tmp_path, monkeypatch):
        # Override data dir for isolation
        from app.services import storage as storage_mod
        monkeypatch.setattr(storage_mod, "DATA_DIR", tmp_path)
        monkeypatch.setattr(storage_mod, "COMICS_DIR", tmp_path / "comics")

        comic = {
            "comic_id": "test-123",
            "title": "Test Comic",
            "source": "mangadex",
            "source_url": "https://mangadex.org/title/test-123",
            "chapters": [],
        }
        save_library({"version": 1, "comics": [comic]})

        response = client.get("/api/library")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["comics"][0]["title"] == "Test Comic"

    def test_get_comic_detail(self, tmp_path, monkeypatch):
        from app.services import storage as storage_mod
        monkeypatch.setattr(storage_mod, "DATA_DIR", tmp_path)
        monkeypatch.setattr(storage_mod, "COMICS_DIR", tmp_path / "comics")

        comic = {
            "comic_id": "test-456",
            "title": "Detail Comic",
            "source": "mangadex",
            "chapters": [],
        }
        save_library({"version": 1, "comics": [comic]})

        response = client.get("/api/library/test-456")
        assert response.status_code == 200
        assert response.json()["title"] == "Detail Comic"


class TestSettings:
    def test_get_settings(self):
        response = client.get("/api/settings")
        assert response.status_code == 200
        data = response.json()
        assert data["app_name"] == "MangoToon"
        assert data["theme"] == "dark"

    def test_post_settings(self):
        payload = {
            "app_name": "MangoToon",
            "library_path": "./data/comics",
            "download_concurrency": 3,
            "theme": "dark",
            "language": "en",
        }
        response = client.post("/api/settings", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["download_concurrency"] == 3

        # Verify persistence
        response = client.get("/api/settings")
        assert response.json()["download_concurrency"] == 3

    def test_post_settings_invalid_concurrency(self):
        payload = {
            "app_name": "MangoToon",
            "download_concurrency": 10,  # Above max of 5
            "theme": "dark",
            "language": "en",
        }
        response = client.post("/api/settings", json=payload)
        assert response.status_code == 422
