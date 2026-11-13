import io
import tomllib
from pathlib import Path

from dash.cache import default_cache_dir
from dash.cli import build_parser, main
from dash.config import APP_NAME, default_config_path

ROOT = Path(__file__).parent.parent


def test_command_name_is_pdash():
    assert APP_NAME == "pdash" and build_parser().prog == "pdash"


def test_installed_script_is_pdash_and_not_dash():
    scripts = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["scripts"]
    assert scripts == {"pdash": "dash.cli:main"}


def test_error_messages_are_prefixed_with_the_command_name(tmp_path):
    err = io.StringIO()
    code = main(["--config", str(tmp_path / "nope.toml")], stdout=io.StringIO(), stderr=err)
    assert code != 0 and err.getvalue().startswith("pdash: ")


def test_data_directories_use_the_new_name():
    assert default_config_path().parent.name == "pdash"
    assert default_cache_dir().name == "pdash"


def test_header_starts_with_the_command_name(tmp_path, monkeypatch):
    from datetime import datetime

    from dash.cache import Cache
    from dash.registry import Registry

    monkeypatch.setenv("NO_COLOR", "1")
    cfg = tmp_path / "c.toml"
    cfg.write_text("")
    out = io.StringIO()
    main(["--config", str(cfg)], stdout=out, registry=Registry(), cache=Cache(tmp_path / "x"),
         clock=lambda: datetime(2026, 11, 12, 14, 3))
    assert out.getvalue().splitlines()[0].startswith("pdash - Thursday 2026-11-12")
