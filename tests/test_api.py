"""Tests for the baseline API."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["app"] == "MangoToon"


def test_root_serves_library_page():
    response = client.get("/")

    assert response.status_code == 200
    assert "MangoToon" in response.text


def test_settings_page_serves_settings_html():
    response = client.get("/settings")

    assert response.status_code == 200
    assert "Settings" in response.text


def test_history_page_serves_history_html():
    response = client.get("/history")

    assert response.status_code == 200
    assert "History" in response.text
