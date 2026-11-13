import pytest

from dash.config import load_config
from dash.init_files import STARTER_HABITS, SetupError, create_if_absent, run_init, starter_config
from dash.widgets.habits import HabitsWidget


def test_creates_file_with_content(tmp_path):
    out = create_if_absent(tmp_path / "a.toml", "hello\n")
    assert out.created and (tmp_path / "a.toml").read_text() == "hello\n"
    assert [p.name for p in tmp_path.iterdir()] == ["a.toml"]  # no temp file left behind


def test_existing_file_is_skipped_and_untouched(tmp_path):
    p = tmp_path / "a.toml"
    p.write_text("mine")
    out = create_if_absent(p, "starter")
    assert not out.created and p.read_text() == "mine"
    assert [x.name for x in tmp_path.iterdir()] == ["a.toml"]


def test_creates_missing_parent_directories(tmp_path):
    p = tmp_path / "x" / "y" / "z.toml"
    assert create_if_absent(p, "c").created and p.read_text() == "c"


def test_one_skipped_and_one_created(tmp_path):
    cfg, habits = tmp_path / "config.toml", tmp_path / "habits.toml"
    cfg.write_text("keep me")
    outcomes = run_init(cfg, habits)
    assert [(o.path.name, o.created) for o in outcomes] == [("config.toml", False), ("habits.toml", True)]
    assert cfg.read_text() == "keep me" and habits.read_text() == STARTER_HABITS


def test_everything_exists_nothing_written(tmp_path):
    cfg, habits = tmp_path / "config.toml", tmp_path / "habits.toml"
    cfg.write_text("a")
    habits.write_text("b")
    assert [o.created for o in run_init(cfg, habits)] == [False, False]
    assert (cfg.read_text(), habits.read_text()) == ("a", "b")


def test_link_failure_leaves_nothing_behind(tmp_path, monkeypatch):
    def boom(src, dst):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr("dash.init_files.os.link", boom)
    with pytest.raises(SetupError, match="Permission denied") as exc:
        create_if_absent(tmp_path / "a.toml", "x")
    assert str(tmp_path / "a.toml") in str(exc.value) and list(tmp_path.iterdir()) == []


def test_write_failure_leaves_nothing_behind(tmp_path, monkeypatch):
    def boom(fd, *a, **k):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr("dash.init_files.os.fdopen", boom)
    with pytest.raises(SetupError, match="No space"):
        create_if_absent(tmp_path / "a.toml", "x")
    assert list(tmp_path.iterdir()) == []


def test_unwritable_directory_is_a_clear_error(tmp_path):
    ro = tmp_path / "ro"
    ro.mkdir()
    ro.chmod(0o500)
    try:
        with pytest.raises(SetupError, match=str(ro / "a.toml")):
            create_if_absent(ro / "a.toml", "x")
    finally:
        ro.chmod(0o700)


def test_starter_config_is_valid_and_enables_three_widgets(tmp_path):
    p = tmp_path / "c.toml"
    p.write_text(starter_config())
    cfg = load_config(p)
    assert [w.id for w in cfg.widgets] == ["weather", "github", "habits"]
    assert cfg.widgets[0].options["location"] == "London"
    assert cfg.widgets[2].options["path"] == "~/habits.toml"


@pytest.mark.parametrize("city", ["Culiacan", 'Saint "Quote" City', "back\\slash", "Zürich", "a # b"])
def test_location_is_quoted_safely(tmp_path, city):
    p = tmp_path / "c.toml"
    p.write_text(starter_config(city))
    assert load_config(p).widgets[0].options["location"] == city
    assert "change this" not in p.read_text()  # a chosen location drops the placeholder note


def test_starter_habits_parse_with_no_completions(tmp_path):
    from datetime import date

    p = tmp_path / "h.toml"
    p.write_text(STARTER_HABITS)
    data = HabitsWidget(today=lambda: date(2026, 11, 13)).fetch({"path": str(p)})
    assert [h["name"] for h in data["habits"]] == ["Drink water", "Read", "Exercise"]
    assert all(not h["done_today"] and h["streak"] == 0 for h in data["habits"])
