"""Tests for library API endpoints"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestLibraryEndpoints:
    def test_list_library_empty(self):
        response = client.get("/api/library")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_add_comic_invalid_url_scheme(self):
        response = client.post("/api/library/add", json={"url": "ftp://evil.com"})
        assert response.status_code == 400
        assert "HTTP/HTTPS" in response.json()["detail"]

    def test_add_comic_private_ip(self):
        response = client.post("/api/library/add", json={"url": "http://127.0.0.1:8080"})
        assert response.status_code == 400
        assert "Private IP" in response.json()["detail"]

    def test_add_comic_localhost(self):
        response = client.post("/api/library/add", json={"url": "http://localhost:8080"})
        assert response.status_code == 400
        assert "Private IP" in response.json()["detail"]

    def test_add_comic_aws_metadata(self):
        response = client.post("/api/library/add", json={"url": "http://169.254.169.254/latest/meta-data"})
        assert response.status_code == 400
        assert "Cloud metadata" in response.json()["detail"]

    def test_add_comic_with_credentials(self):
        response = client.post("/api/library/add", json={"url": "http://user:pass@evil.com"})
        assert response.status_code == 400
        assert "credentials" in response.json()["detail"]

    def test_add_comic_invalid_url(self):
        response = client.post("/api/library/add", json={"url": "not-a-url"})
        assert response.status_code == 422  # FastAPI validation error

    def test_add_comic_valid_url(self):
        response = client.post("/api/library/add", json={
            "url": "https://mangadex.org/title/abc123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "comic_id" in data
        assert data["status"] == "pending"

    def test_get_comic_not_found(self):
        response = client.get("/api/library/nonexistent-id")
        assert response.status_code == 404

    def test_delete_comic_not_found(self):
        response = client.delete("/api/library/nonexistent-id")
        assert response.status_code == 404


class TestReaderEndpoints:
    def test_get_progress_not_found(self):
        response = client.get("/api/reader/nonexistent/progress")
        assert response.status_code == 404

    def test_update_progress_not_found(self):
        response = client.post("/api/reader/nonexistent/progress", json={
            "chapter": 1,
            "page": 5,
            "completed": False
        })
        assert response.status_code == 404

    def test_serve_page_not_found(self):
        response = client.get("/api/reader/nonexistent/1/1")
        assert response.status_code == 404


class TestSettingsEndpoints:
    def test_get_settings(self):
        response = client.get("/api/settings")
        assert response.status_code == 200
        data = response.json()
        assert "library_path" in data
        assert "scraper_concurrency" in data

    def test_update_settings(self):
        response = client.post("/api/settings", json={"any": "data"})
        assert response.status_code == 200
        assert response.json()["status"] == "updated"