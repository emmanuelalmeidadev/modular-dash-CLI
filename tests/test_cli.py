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
