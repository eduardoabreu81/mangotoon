"""Local JSON storage service with atomic writes."""

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from app.core.config import settings


DATA_DIR = Path(settings.data_dir)
COMICS_DIR = DATA_DIR / "comics"


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    COMICS_DIR.mkdir(parents=True, exist_ok=True)


def _atomic_write_json(path: Path, data: Any) -> None:
    """Write JSON atomically using a temp file and rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".tmp",
        dir=str(path.parent),
        delete=False,
    ) as f:
        json.dump(data, f, indent=2, default=_json_default)
        f.write("\n")
        temp_path = Path(f.name)
    shutil.move(str(temp_path), str(path))


def _json_default(obj: Any) -> Any:
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    _atomic_write_json(path, data)


# Library


def get_library_path() -> Path:
    return DATA_DIR / "library.json"


def load_library() -> dict[str, Any]:
    _ensure_data_dir()
    path = get_library_path()
    data = read_json(path, {"version": 1, "comics": []})
    if isinstance(data, list):
        return {"version": 1, "comics": data}
    return data


def save_library(data: dict[str, Any]) -> None:
    _ensure_data_dir()
    write_json(get_library_path(), data)


def get_comic(comic_id: str) -> dict[str, Any] | None:
    library = load_library()
    for comic in library.get("comics", []):
        if comic.get("comic_id") == comic_id:
            return comic
    return None


def add_comic(comic: dict[str, Any]) -> None:
    library = load_library()
    comics = library.get("comics", [])
    for i, existing in enumerate(comics):
        if existing.get("comic_id") == comic.get("comic_id"):
            comics[i] = comic
            break
    else:
        comics.append(comic)
    library["comics"] = comics
    save_library(library)


def delete_comic(comic_id: str) -> bool:
    library = load_library()
    comics = library.get("comics", [])
    original_len = len(comics)
    comics = [c for c in comics if c.get("comic_id") != comic_id]
    if len(comics) == original_len:
        return False
    library["comics"] = comics
    save_library(library)
    # Remove local comic folder
    comic_dir = COMICS_DIR / comic_id
    if comic_dir.exists():
        shutil.rmtree(comic_dir)
    return True


# Settings


def get_settings_path() -> Path:
    return DATA_DIR / "settings.json"


def load_settings() -> dict[str, Any]:
    _ensure_data_dir()
    defaults = {
        "app_name": settings.app_name,
        "library_path": str(settings.data_dir / "comics"),
        "download_concurrency": 2,
        "rate_limit_per_domain": 1.0,
        "reader_default_fit": "fit-width",
        "reader_auto_advance": False,
        "reader_auto_advance_delay": 4,
        "reader_show_progress_bar": True,
        "download_auto_start": True,
        "download_default_chapters": "all",
        "theme": "dark",
        "language": "en",
        "llm_provider": "",
        "llm_model": "",
        "llm_api_key": "",
    }
    stored = read_json(get_settings_path(), {})
    # Merge stored over defaults
    merged = {**defaults, **stored}
    return merged


def save_settings(data: dict[str, Any]) -> None:
    _ensure_data_dir()
    write_json(get_settings_path(), data)


# History


def get_history_path() -> Path:
    return DATA_DIR / "history.json"


def load_history() -> dict[str, Any]:
    _ensure_data_dir()
    data = read_json(get_history_path(), {"version": 1, "items": []})
    # Guard against corrupted history files that are arrays instead of dicts
    if isinstance(data, list):
        return {"version": 1, "items": data}
    if not isinstance(data, dict):
        return {"version": 1, "items": []}
    return data


def save_history(data: dict[str, Any]) -> None:
    _ensure_data_dir()
    write_json(get_history_path(), data)


# Comic metadata


def get_comic_metadata_path(comic_id: str) -> Path:
    return COMICS_DIR / comic_id / "metadata.json"


def load_comic_metadata(comic_id: str) -> dict[str, Any] | None:
    path = get_comic_metadata_path(comic_id)
    if not path.exists():
        return None
    return read_json(path, {})


def save_comic_metadata(comic_id: str, data: dict[str, Any]) -> None:
    path = get_comic_metadata_path(comic_id)
    _atomic_write_json(path, data)
