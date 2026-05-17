import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_LIBRARY: dict[str, Any] = {"version": 1, "comics": []}
DEFAULT_HISTORY: dict[str, Any] = {"version": 1, "items": []}
DEFAULT_SETTINGS: dict[str, Any] = {
    "app_name": "MangoToon",
    "library_path": "./data/comics",
    "download_concurrency": 2,
    "theme": "dark",
    "language": "en",
}


def write_json_if_missing(path: Path, data: Any) -> None:
    if not path.exists():
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def init_data(data_dir: Path = Path("data")) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "comics").mkdir(parents=True, exist_ok=True)

    write_json_if_missing(data_dir / "library.json", DEFAULT_LIBRARY)
    write_json_if_missing(data_dir / "history.json", DEFAULT_HISTORY)
    write_json_if_missing(data_dir / "settings.json", DEFAULT_SETTINGS)


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize local application data files.")
    parser.add_argument("--data-dir", type=Path, default=Path("data"), help="Directory where local data is stored.")
    args = parser.parse_args()

    init_data(args.data_dir)
    print(f"Initialized data directory: {args.data_dir}")


if __name__ == "__main__":
    main()
