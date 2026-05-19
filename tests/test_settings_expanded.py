from fastapi.testclient import TestClient

from app.main import app
from app.services import storage


def setup_settings_storage(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path)
    monkeypatch.setattr(storage, "COMICS_DIR", tmp_path / "comics")


def test_get_settings_returns_all_default_settings(tmp_path, monkeypatch):
    setup_settings_storage(tmp_path, monkeypatch)

    response = TestClient(app).get("/api/settings")

    assert response.status_code == 200
    data = response.json()
    assert data["reader_default_fit"] == "fit-width"
    assert data["reader_auto_advance"] is False
    assert data["reader_auto_advance_delay"] == 4
    assert data["reader_show_progress_bar"] is True
    assert data["download_auto_start"] is True
    assert data["download_default_chapters"] == "all"
    assert data["theme"] == "dark"
    assert data["mangadex_language"] == "en"


def test_post_settings_updates_expanded_settings(tmp_path, monkeypatch):
    setup_settings_storage(tmp_path, monkeypatch)
    payload = TestClient(app).get("/api/settings").json()
    payload.update(
        {
            "reader_default_fit": "fit-screen",
            "reader_auto_advance": True,
            "reader_auto_advance_delay": 8,
            "reader_show_progress_bar": False,
            "download_auto_start": False,
            "download_default_chapters": "unread",
            "theme": "auto",
            "mangadex_language": "pt-br",
        }
    )

    response = TestClient(app).post("/api/settings", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["reader_default_fit"] == "fit-screen"
    assert data["reader_auto_advance"] is True
    assert data["reader_auto_advance_delay"] == 8
    assert data["reader_show_progress_bar"] is False
    assert data["download_auto_start"] is False
    assert data["download_default_chapters"] == "unread"
    assert data["theme"] == "auto"
    assert data["mangadex_language"] == "pt-br"


def test_post_settings_rejects_invalid_values(tmp_path, monkeypatch):
    setup_settings_storage(tmp_path, monkeypatch)
    payload = TestClient(app).get("/api/settings").json()
    payload["reader_default_fit"] = "stretch"
    payload["download_default_chapters"] = "latest"
    payload["theme"] = "blue"
    payload["mangadex_language"] = "invalid"

    response = TestClient(app).post("/api/settings", json=payload)

    assert response.status_code == 422
    locations = {error["loc"][-1] for error in response.json()["detail"]}
    assert {"reader_default_fit", "download_default_chapters", "theme", "mangadex_language"}.issubset(locations)
