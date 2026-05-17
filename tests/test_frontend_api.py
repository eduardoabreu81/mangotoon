"""Frontend API client contract tests.

These tests use FastAPI's TestClient to verify the backend routes consumed by
frontend/js/api.js and frontend/js/app.js.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import storage


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path)
    monkeypatch.setattr(storage, "COMICS_DIR", tmp_path / "comics")
    storage.save_library({"version": 1, "comics": []})
    storage.save_settings(
        {
            "app_name": "MangoToon",
            "library_path": str(tmp_path / "comics"),
            "download_concurrency": 2,
            "rate_limit_per_domain": 1.0,
            "theme": "dark",
            "language": "en",
            "llm_provider": "",
            "llm_model": "",
            "llm_api_key": "",
        }
    )
    return TestClient(app)


@pytest.fixture()
def sample_comic():
    return {
        "comic_id": "comic-001",
        "title": "Sample Comic",
        "source": "local",
        "source_url": "https://example.test/comics/sample",
        "source_id": "sample",
        "description": "A sample comic for API contract tests.",
        "cover_url": "",
        "cover_local": "",
        "status": "pending",
        "chapters": [
            {
                "chapter_id": "chapter-001",
                "title": "Chapter One",
                "chapter_number": "1",
                "language": "en",
                "pages": 12,
                "status": "downloaded",
                "downloaded_pages": 12,
            },
            {
                "chapter_id": "chapter-002",
                "title": "Chapter Two",
                "chapter_number": "2",
                "language": "en",
                "pages": 10,
                "status": "not_downloaded",
                "downloaded_pages": 0,
            },
        ],
    }


def test_health_endpoint_connection(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "app": "MangoToon",
        "version": "0.1.0",
    }


def test_library_fetch_matches_frontend_shape(client, sample_comic):
    storage.save_library({"version": 1, "comics": [sample_comic]})

    response = client.get("/api/library")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["comics"]) == 1
    assert data["comics"][0]["comic_id"] == "comic-001"
    assert data["comics"][0]["title"] == "Sample Comic"
    assert data["comics"][0]["source"] == "local"
    assert data["comics"][0]["status"] == "pending"


def test_comic_detail_fetch(client, sample_comic):
    storage.save_library({"version": 1, "comics": [sample_comic]})

    response = client.get("/api/library/comic-001")

    assert response.status_code == 200
    data = response.json()
    assert data["comic_id"] == "comic-001"
    assert data["title"] == "Sample Comic"
    assert len(data["chapters"]) == 2
    assert data["chapters"][0]["chapter_id"] == "chapter-001"


def test_settings_get_and_post(client):
    get_response = client.get("/api/settings")

    assert get_response.status_code == 200
    current = get_response.json()
    assert current["app_name"] == "MangoToon"
    assert current["theme"] == "dark"

    updated = {
        **current,
        "download_concurrency": 4,
        "theme": "light",
        "language": "en",
    }
    post_response = client.post("/api/settings", json=updated)

    assert post_response.status_code == 200
    saved = post_response.json()
    assert saved["download_concurrency"] == 4
    assert saved["theme"] == "light"

    verify_response = client.get("/api/settings")
    assert verify_response.status_code == 200
    assert verify_response.json()["download_concurrency"] == 4
    assert verify_response.json()["theme"] == "light"


def test_api_error_handling_returns_json_detail_for_missing_comic(client):
    response = client.get("/api/library/missing-comic")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


def test_api_error_handling_returns_validation_details_for_bad_settings(client):
    response = client.post(
        "/api/settings",
        json={
            "app_name": "MangoToon",
            "library_path": "./data/comics",
            "download_concurrency": 99,
            "theme": "dark",
            "language": "en",
        },
    )

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert data["detail"][0]["loc"][-1] == "download_concurrency"
