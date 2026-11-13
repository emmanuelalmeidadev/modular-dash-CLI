import io
import json

import pytest

from dash.cache import Cache
from dash.cli import main
from dash.registry import Registry


def run(tmp_path, fake_widget, config_text, argv=(), widgets=(), clock=None):
    cfg = tmp_path / "config.toml"
    if config_text is not None:
        cfg.write_text(config_text)
    reg = Registry()
    for w in widgets:
        reg.register(w)
    out, err = io.StringIO(), io.StringIO()
    code = main(["--config", str(cfg), *argv], registry=reg, cache=Cache(tmp_path / "c"), stdout=out, stderr=err, clock=clock)
    return code, out.getvalue(), err.getvalue()


def test_default_run_renders_in_config_order_and_exits_zero(tmp_path, fake_widget, monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    code, out, _ = run(tmp_path, fake_widget, '[[widgets]]\nid = "b"\n[[widgets]]\nid = "a"\n',
                       widgets=[fake_widget("a"), fake_widget("b")])
    assert code == 0 and out.index("B") < out.index("A")


def test_json_flag_prints_only_json(tmp_path, fake_widget):
    code, out, err = run(tmp_path, fake_widget, '[[widgets]]\nid = "a"\n', ["--json"], [fake_widget("a")])
    doc = json.loads(out)
    assert code == 0 and err == "" and [w["id"] for w in doc["widgets"]] == ["a"]


def test_partial_failure_still_exits_zero_in_both_modes(tmp_path, fake_widget, monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")

    def boom(o):
        raise RuntimeError("kaput")

    widgets = [fake_widget("bad", boom), fake_widget("good")]
    cfg = '[[widgets]]\nid = "bad"\n[[widgets]]\nid = "good"\n'
    code, out, _ = run(tmp_path, fake_widget, cfg, ["--json"], widgets)
    doc = json.loads(out)
    assert code == 0 and [w["status"] for w in doc["widgets"]] == ["error", "ok"]
    code, out, _ = run(tmp_path, fake_widget, cfg, [], [fake_widget("bad", boom), fake_widget("good")])
    assert code == 0 and "kaput" in out


def test_invalid_config_exits_nonzero_with_message(tmp_path, fake_widget):
    code, out, err = run(tmp_path, fake_widget, "[[widgets", [])
    assert code != 0 and out == "" and "invalid config" in err


def test_missing_config_names_expected_path(tmp_path, fake_widget):
    code, out, err = run(tmp_path, fake_widget, None, [])
    assert code != 0 and "config.toml" in err


def test_refresh_flag_bypasses_cache(tmp_path, fake_widget):
    w = fake_widget("a")
    cfg = '[[widgets]]\nid = "a"\n'
    run(tmp_path, fake_widget, cfg, ["--json"], [w])
    run(tmp_path, fake_widget, cfg, ["--json"], [w])
    assert w.calls == 1
    run(tmp_path, fake_widget, cfg, ["--json", "--refresh"], [w])
    assert w.calls == 2


def test_header_and_json_agree_on_one_timestamp(tmp_path, fake_widget, monkeypatch):
    from datetime import datetime, timedelta, timezone

    now = datetime(2026, 11, 12, 14, 3, 7, tzinfo=timezone(timedelta(hours=-7)))
    calls = []

    def clock():
        calls.append(1)
        return now

    monkeypatch.setenv("NO_COLOR", "1")
    cfg = '[[widgets]]\nid = "a"\n'
    _, out, _ = run(tmp_path, fake_widget, cfg, [], [fake_widget("a")], clock)
    assert "Thursday 2026-11-12, 14:03" in out and len(calls) == 1
    _, out, _ = run(tmp_path, fake_widget, cfg, ["--json"], [fake_widget("a")], clock)
    assert json.loads(out)["generated_at"] == "2026-11-12T14:03:07-07:00"


# ---- habit done ----

from datetime import date, datetime as _dt, timezone as _tz

HABITS = '[[habits]]\nname = "Drink water"\ndone = ["2026-11-11"]\n[[habits]]\nname = "Read"\n'
NOW = _dt(2026, 11, 12, 9, 0, tzinfo=_tz.utc)


def habit_run(tmp_path, argv, config_text=None, habits_text=HABITS, config_first=True):
    habits = tmp_path / "habits.toml"
    if habits_text is not None:
        habits.write_text(habits_text)
    cfg = tmp_path / "config.toml"
    cfg.write_text(config_text if config_text is not None else
                   f'[[widgets]]\nid = "habits"\n[widgets.options]\npath = "{habits}"\n')
    out, err = io.StringIO(), io.StringIO()
    prefix = ["--config", str(cfg)]
    full = (prefix + argv) if config_first else (argv + prefix)
    code = main(full, stdout=out, stderr=err, clock=lambda: NOW, registry=Registry(), cache=Cache(tmp_path / "c"))
    return code, out.getvalue(), err.getvalue(), habits



@pytest.mark.parametrize("config_first", [True, False])
def test_habit_done_marks_today_with_config_either_side(tmp_path, config_first):
    code, out, err, habits = habit_run(tmp_path, ["habit", "done", "drink water"], config_first=config_first)
    assert code == 0 and err == "" and "Recorded: Drink water done on 2026-11-12" in out
    assert "2026-11-12" in habits.read_text()


def test_habit_done_backfill_and_idempotent(tmp_path):
    code, out, _, habits = habit_run(tmp_path, ["habit", "done", "Read", "--date", "2026-11-10"])
    assert code == 0 and "2026-11-10" in habits.read_text()
    code, out, _, _ = habit_run(tmp_path, ["habit", "done", "Read", "--date", "2026-11-10"], habits_text=habits.read_text())
    assert code == 0 and "Already recorded" in out and habits.read_text().count("2026-11-10") == 1


def test_habit_done_unknown_name_exit_nonzero_file_unchanged(tmp_path):
    code, out, err, habits = habit_run(tmp_path, ["habit", "done", "Meditate"])
    assert code == 1 and out == "" and "Drink water" in err and habits.read_text() == HABITS


@pytest.mark.parametrize("date_arg", ["2026-11-13", "yesterday"])
def test_habit_done_bad_dates_refused(tmp_path, date_arg):
    code, _, err, habits = habit_run(tmp_path, ["habit", "done", "Read", "--date", date_arg])
    assert code == 1 and err and habits.read_text() == HABITS


def test_habit_done_without_habits_widget(tmp_path):
    code, _, err, _ = habit_run(tmp_path, ["habit", "done", "Read"], config_text='[[widgets]]\nid = "weather"\n')
    assert code == 2 and "habits widget" in err and "path" in err


def test_habit_done_widget_without_path(tmp_path):
    code, _, err, _ = habit_run(tmp_path, ["habit", "done", "Read"], config_text='[[widgets]]\nid = "habits"\n')
    assert code == 2 and "path" in err


def test_habit_done_missing_file_names_path_and_creates_nothing(tmp_path):
    code, _, err, habits = habit_run(tmp_path, ["habit", "done", "Read"], habits_text=None)
    assert code == 1 and str(habits) in err and not habits.exists()


def test_habit_done_invalid_config(tmp_path):
    code, _, err, _ = habit_run(tmp_path, ["habit", "done", "Read"], config_text="[[widgets")
    assert code == 2 and "invalid config" in err


def test_habit_done_requires_a_name():
    with pytest.raises(SystemExit):
        main(["habit", "done"])


def test_plain_dash_and_json_unchanged_by_subcommands(tmp_path, fake_widget):
    code, out, err = run(tmp_path, fake_widget, '[[widgets]]\nid = "a"\n', ["--json"], [fake_widget("a")], lambda: NOW)
    doc = json.loads(out)
    assert code == 0 and err == "" and list(doc) == ["generated_at", "widgets"]


# ---- init ----

def init_run(tmp_path, monkeypatch, argv):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))  # never touch the real home directory
    (tmp_path / "home").mkdir(exist_ok=True)
    out, err = io.StringIO(), io.StringIO()
    code = main(argv, stdout=out, stderr=err, clock=lambda: NOW)
    return code, out.getvalue(), err.getvalue()


def test_init_creates_both_files_and_dashboard_runs_after(tmp_path, monkeypatch):
    cfg = tmp_path / "conf" / "my.toml"
    code, out, err = init_run(tmp_path, monkeypatch, ["init", "--config", str(cfg)])
    habits = tmp_path / "home" / "habits.toml"
    assert code == 0 and err == "" and cfg.exists() and habits.exists()
    assert f"Created: {cfg}" in out and f"Created: {habits}" in out
    # plain `pdash` right after init exits 0 (widgets are faked so no network is used)
    from dash.cache import Cache
    from dash.registry import Registry
    monkeypatch.setenv("NO_COLOR", "1")
    o2 = io.StringIO()
    assert main(["--config", str(cfg)], stdout=o2, stderr=io.StringIO(), registry=Registry(),
                cache=Cache(tmp_path / "c"), clock=lambda: NOW) == 0


def test_init_default_config_path_lives_under_home(tmp_path, monkeypatch):
    code, out, _ = init_run(tmp_path, monkeypatch, ["init"])
    from dash.config import default_config_path
    assert code == 0 and str(default_config_path()).startswith(str(tmp_path / "home"))
    assert default_config_path().exists()


def test_init_skips_existing_config_and_still_creates_habits(tmp_path, monkeypatch):
    cfg = tmp_path / "my.toml"
    cfg.write_text("mine")
    code, out, _ = init_run(tmp_path, monkeypatch, ["init", "--config", str(cfg)])
    assert code == 0 and cfg.read_text() == "mine"
    assert f"Skipped (already exists): {cfg}" in out and "Created:" in out


def test_init_everything_exists_exit_zero(tmp_path, monkeypatch):
    cfg = tmp_path / "my.toml"
    init_run(tmp_path, monkeypatch, ["init", "--config", str(cfg)])
    before = cfg.read_bytes()
    code, out, _ = init_run(tmp_path, monkeypatch, ["init", "--config", str(cfg)])
    assert code == 0 and out.count("Skipped (already exists)") == 2 and "Created:" not in out
    assert cfg.read_bytes() == before


def test_init_location_option(tmp_path, monkeypatch):
    from dash.config import load_config
    cfg = tmp_path / "my.toml"
    code, out, _ = init_run(tmp_path, monkeypatch, ["init", "--config", str(cfg), "--location", "Culiacan"])
    assert code == 0 and load_config(cfg).widgets[0].options["location"] == "Culiacan"
    assert "weather location" not in out  # no "edit your location" step when it was supplied


def test_init_next_steps_without_location_mention_it(tmp_path, monkeypatch):
    _, out, _ = init_run(tmp_path, monkeypatch, ["init", "--config", str(tmp_path / "my.toml")])
    assert "weather location" in out


def test_init_next_steps_mention_token_options_and_never_a_token(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_SECRETVALUE123")
    _, out, err = init_run(tmp_path, monkeypatch, ["init", "--config", str(tmp_path / "my.toml")])
    assert "GITHUB_TOKEN" in out and "token_cmd" in out
    assert "ghp_SECRETVALUE123" not in out + err and "ghp_SECRETVALUE123" not in (tmp_path / "my.toml").read_text()


def test_init_failure_exits_nonzero_names_path_no_partial_file(tmp_path, monkeypatch):
    ro = tmp_path / "ro"
    ro.mkdir()
    ro.chmod(0o500)
    try:
        code, out, err = init_run(tmp_path, monkeypatch, ["init", "--config", str(ro / "sub" / "my.toml")])
    finally:
        ro.chmod(0o700)
    assert code == 1 and err.startswith("pdash: ") and str(ro) in err
    assert not (ro / "sub").exists()


@pytest.mark.parametrize("bad", ["", "   "])
def test_init_rejects_blank_location(tmp_path, monkeypatch, bad):
    monkeypatch.setenv("HOME", str(tmp_path))
    with pytest.raises(SystemExit):
        main(["init", "--config", str(tmp_path / "x.toml"), "--location", bad])
    assert not (tmp_path / "x.toml").exists()
