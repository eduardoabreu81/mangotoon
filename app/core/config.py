import json
from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    library_path: Path = Path("comics")
    config_path: Path = Path("config.json")
    library_db_path: Path = Path("library.json")

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://openrouter.ai/api/v1"

    scraper_concurrency: int = 4
    scraper_rate_limit: float = 1.0
    scraper_retry_attempts: int = 3

    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    model_config = {"env_prefix": "COMICLIB_", "env_file": ".env"}

    def load_library(self) -> list[dict[str, Any]]:
        if self.library_db_path.exists():
            return json.loads(self.library_db_path.read_text())
        return []

    def save_library(self, data: list[dict[str, Any]]) -> None:
        self.library_db_path.write_text(json.dumps(data, indent=2, default=str))

    def load_comic_metadata(self, comic_id: str) -> dict[str, Any]:
        meta_path = self.library_path / comic_id / "metadata.json"
        if meta_path.exists():
            return json.loads(meta_path.read_text())
        return {}

    def save_comic_metadata(self, comic_id: str, data: dict[str, Any]) -> None:
        comic_dir = self.library_path / comic_id
        comic_dir.mkdir(parents=True, exist_ok=True)
        meta_path = comic_dir / "metadata.json"
        meta_path.write_text(json.dumps(data, indent=2, default=str))


settings = Settings()
