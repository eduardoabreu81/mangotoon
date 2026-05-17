import json

from scripts.init_data import init_data


def test_init_data_creates_expected_files(tmp_path):
    init_data(tmp_path)

    assert (tmp_path / "library.json").exists()
    assert (tmp_path / "history.json").exists()
    assert (tmp_path / "settings.json").exists()
    assert (tmp_path / "comics").is_dir()

    assert json.loads((tmp_path / "library.json").read_text(encoding="utf-8")) == {"version": 1, "comics": []}
    assert json.loads((tmp_path / "history.json").read_text(encoding="utf-8")) == {"version": 1, "items": []}
    assert json.loads((tmp_path / "settings.json").read_text(encoding="utf-8"))["app_name"] == "MangoToon"
