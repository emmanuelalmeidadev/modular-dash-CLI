from datetime import date

import pytest

from dash.widgets.habits import HabitsError, HabitsWidget, current_streak

TODAY = date(2026, 11, 11)


def widget():
    return HabitsWidget(today=lambda: TODAY)


def write(tmp_path, text):
    p = tmp_path / "habits.toml"
    p.write_text(text)
    return p


def test_lists_all_habits_with_status(tmp_path):
    p = write(tmp_path, """
[[habits]]
name = "Read"
done = ["2026-11-09", "2026-11-10", "2026-11-11"]
[[habits]]
name = "Run"
done = []
""")
    data = widget().fetch({"path": str(p)})
    assert [h["name"] for h in data["habits"]] == ["Read", "Run"]
    assert data["habits"][0] == {"name": "Read", "done_today": True, "streak": 3}
    assert data["habits"][1] == {"name": "Run", "done_today": False, "streak": 0}


def test_streak_continues_through_today():
    days = {date(2026, 11, 9), date(2026, 11, 10), date(2026, 11, 11)}
    assert current_streak(days, TODAY) == 3


def test_today_not_yet_done_keeps_streak():
    assert current_streak({date(2026, 11, 9), date(2026, 11, 10)}, TODAY) == 2


def test_gap_breaks_streak():
    assert current_streak({date(2026, 11, 11), date(2026, 11, 9)}, TODAY) == 1


def test_streak_dead_if_yesterday_missed_and_today_not_done():
    assert current_streak({date(2026, 11, 8)}, TODAY) == 0


def test_native_toml_dates_accepted(tmp_path):
    p = write(tmp_path, '[[habits]]\nname = "A"\ndone = [2026-11-10, 2026-11-11]\n')
    assert widget().fetch({"path": str(p)})["habits"][0]["streak"] == 2


def test_missing_file_names_path(tmp_path):
    p = tmp_path / "nope.toml"
    with pytest.raises(HabitsError, match=str(p)):
        widget().fetch({"path": str(p)})


def test_malformed_file_reports_parse_problem(tmp_path):
    p = write(tmp_path, "[[habits")
    with pytest.raises(HabitsError, match="cannot parse"):
        widget().fetch({"path": str(p)})


def test_missing_path_option():
    with pytest.raises(HabitsError, match="path"):
        widget().fetch({})


def test_bad_date_reports_habit(tmp_path):
    p = write(tmp_path, '[[habits]]\nname = "A"\ndone = ["yesterday"]\n')
    with pytest.raises(HabitsError, match="'A'"):
        widget().fetch({"path": str(p)})


def test_file_is_never_modified(tmp_path):
    p = write(tmp_path, '[[habits]]\nname = "A"\ndone = ["2026-11-11"]\n')
    before = p.read_bytes()
    mtime = p.stat().st_mtime_ns
    widget().fetch({"path": str(p)})
    assert p.read_bytes() == before and p.stat().st_mtime_ns == mtime


def test_documented_example_parses(tmp_path):
    import re
    from pathlib import Path

    doc = (Path(__file__).parent.parent / "docs" / "habits.md").read_text()
    blocks = re.findall(r"```toml\n(.*?)```", doc, re.S)
    example = next(b for b in blocks if "[[habits]]" in b)
    p = write(tmp_path, example)
    habits = widget().fetch({"path": str(p)})["habits"]
    assert [h["name"] for h in habits] == ["Read 20 pages", "Run"]
    assert habits[0]["streak"] == 3


def test_documented_habit_done_commands_work_as_written(tmp_path):
    import io
    import re
    import shlex
    from datetime import datetime, timezone
    from pathlib import Path

    from dash.cache import Cache
    from dash.cli import main
    from dash.registry import Registry

    doc = (Path(__file__).parent.parent / "docs" / "habits.md").read_text()
    example = next(b for b in re.findall(r"```toml\n(.*?)```", doc, re.S) if "[[habits]]" in b and "name =" in b and "id =" not in b)
    habits = write(tmp_path, example)
    cfg = tmp_path / "config.toml"
    cfg.write_text(f'[[widgets]]\nid = "habits"\n[widgets.options]\npath = "{habits}"\n')

    commands = [shlex.split(line) for block in re.findall(r"```bash\n(.*?)```", doc, re.S)
                for line in block.splitlines() if line.startswith("pdash habit done")]
    assert commands, "docs/habits.md must show at least one `pdash habit done` example"
    now = datetime(2026, 11, 12, 9, 0, tzinfo=timezone.utc)
    for argv in commands:
        out, err = io.StringIO(), io.StringIO()
        code = main(["--config", str(cfg), *argv[1:]], stdout=out, stderr=err, clock=lambda: now,
                    registry=Registry(), cache=Cache(tmp_path / "c"))
        assert code == 0, (argv, err.getvalue())
    assert "2026-11-12" in habits.read_text()  # `pdash habit done "Run"` recorded today
