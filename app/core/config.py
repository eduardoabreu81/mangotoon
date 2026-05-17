from pathlib import Path

from pydantic_settings import BaseSettings

APP_NAME = "MangoToon"


class Settings(BaseSettings):
    app_name: str = APP_NAME
    data_dir: Path = Path("data")
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    model_config = {"env_prefix": "APP_", "env_file": ".env"}


settings = Settings()
