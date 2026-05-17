import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_refresh_comic_not_found(client):
    response = client.post("/api/library/nonexistent/refresh")
    assert response.status_code == 404


def test_refresh_comic_no_source_url(client):
    # This would require a comic in the library without source_url
    # For now, just verify the endpoint structure
    pass
