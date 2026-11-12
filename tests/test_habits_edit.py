from datetime import date

import pytest
import tomlkit

from dash.habits_edit import HabitCompletionError, complete, edit_habits_file, parse_day

TODAY = date(2026, 11, 12)

SAMPLE = '''# my habits
[[habits]]
name = "Drink water"
done = ["2026-11-10"]

[[habits]]
name = "Read"   # evening
done = []

[[habits]]
name = "Exercise"
'''


def doc():
    return tomlkit.parse(SAMPLE)


def days(d, index):
    return [str(x) for x in d["habits"][index].get("done", [])]


# ---- 3.2: logic on parsed documents, no filesystem ----

def test_mark_done_today_case_insensitive():
    d = doc()
    r = complete(d, "drink WATER", TODAY)
    assert r.added and r.habit == "Drink water" and r.day == TODAY
    assert days(d, 0) == ["2026-11-10", "2026-11-12"]


def test_backfill_a_specific_day():
    d = doc()
    complete(d, "Read", date(2026, 11, 10))
    assert days(d, 1) == ["2026-11-10"]


def test_idempotent_no_duplicate():
    d = doc()
    complete(d, "Read", TODAY)
    again = complete(d, "Read", TODAY)
    assert again.added is False and days(d, 1) == ["2026-11-12"]


def test_idempotent_against_native_toml_date():
    d = tomlkit.parse('[[habits]]\nname = "A"\ndone = [2026-11-12]\n')
    assert complete(d, "A", TODAY).added is False


def test_habit_without_done_list_gets_one():
    d = doc()
    complete(d, "Exercise", TODAY)
    assert days(d, 2) == ["2026-11-12"]


def test_native_date_style_followed_when_file_uses_it():
    d = tomlkit.parse('[[habits]]\nname = "A"\ndone = [2026-11-10]\n')
    complete(d, "A", TODAY)
    assert "2026-11-12" in tomlkit.dumps(d) and '"2026-11-12"' not in tomlkit.dumps(d)


def test_unknown_name_lists_available():
    with pytest.raises(HabitCompletionError) as exc:
        complete(doc(), "Meditate", TODAY)
    msg = str(exc.value)
    assert "Meditate" in msg and "Drink water" in msg and "Read" in msg and "Exercise" in msg


def test_ambiguous_name_rejected():
    d = tomlkit.parse('[[habits]]\nname = "Read"\n[[habits]]\nname = "read"\n')
    with pytest.raises(HabitCompletionError, match="ambiguous"):
        complete(d, "READ", TODAY)


def test_file_without_habits_rejected():
    with pytest.raises(HabitCompletionError, match="documented format"):
        complete(tomlkit.parse("x = 1\n"), "A", TODAY)


@pytest.mark.parametrize("arg", ["yesterday", "2026-1-5", "20261110", "2026-13-01", "2026-02-30", ""])
def test_malformed_dates_rejected(arg):
    with pytest.raises(HabitCompletionError, match="invalid date"):
        parse_day(arg, TODAY)


def test_future_date_rejected():
    with pytest.raises(HabitCompletionError, match="future"):
        parse_day("2026-11-13", TODAY)


def test_today_and_past_dates_accepted():
    assert parse_day(None, TODAY) == TODAY
    assert parse_day("2026-11-12", TODAY) == TODAY
    assert parse_day("2025-01-01", TODAY) == date(2025, 1, 1)


# ---- 3.3: file behavior ----

def write(tmp_path, text=SAMPLE):
    p = tmp_path / "habits.toml"
    p.write_text(text)
    return p


def test_backup_holds_previous_contents(tmp_path):
    p = write(tmp_path)
    edit_habits_file(p, "Read", TODAY)
    assert (tmp_path / "habits.toml.bak").read_text() == SAMPLE
    assert p.read_text() != SAMPLE


def test_comments_and_other_habits_preserved(tmp_path):
    p = write(tmp_path)
    edit_habits_file(p, "Read", TODAY)
    text = p.read_text()
    assert "# my habits" in text and "# evening" in text
    d = tomlkit.parse(text)
    assert days(d, 0) == ["2026-11-10"] and days(d, 1) == ["2026-11-12"] and days(d, 2) == []
    assert [h["name"] for h in d["habits"]] == ["Drink water", "Read", "Exercise"]


def test_duplicate_date_does_not_write_or_back_up(tmp_path):
    p = write(tmp_path)
    edit_habits_file(p, "Read", TODAY)
    (tmp_path / "habits.toml.bak").unlink()
    before = p.read_bytes()
    r = edit_habits_file(p, "Read", TODAY)
    assert r.added is False and p.read_bytes() == before and not (tmp_path / "habits.toml.bak").exists()


def test_invalid_request_leaves_file_and_no_backup(tmp_path):
    p = write(tmp_path)
    before = p.read_bytes()
    with pytest.raises(HabitCompletionError):
        edit_habits_file(p, "Meditate", TODAY)
    assert p.read_bytes() == before and not (tmp_path / "habits.toml.bak").exists()


def test_missing_file_is_not_created(tmp_path):
    p = tmp_path / "nope.toml"
    with pytest.raises(HabitCompletionError, match=str(p)):
        edit_habits_file(p, "Read", TODAY)
    assert not p.exists() and list(tmp_path.iterdir()) == []


def test_malformed_file_rejected_unchanged(tmp_path):
    p = write(tmp_path, "[[habits")
    with pytest.raises(HabitCompletionError, match="cannot parse"):
        edit_habits_file(p, "Read", TODAY)
    assert p.read_text() == "[[habits"


def test_write_failure_leaves_original_intact(tmp_path, monkeypatch):
    p = write(tmp_path)

    def boom(src, dst):
        raise OSError("disk full")

    monkeypatch.setattr("dash.habits_edit.os.replace", boom)
    with pytest.raises(HabitCompletionError, match="unchanged"):
        edit_habits_file(p, "Read", TODAY)
    assert p.read_text() == SAMPLE
    assert not list(tmp_path.glob("*.tmp"))  # temp file cleaned up


def test_backup_failure_aborts_before_writing(tmp_path, monkeypatch):
    p = write(tmp_path)

    def boom(src, dst):
        raise OSError("read-only")

    monkeypatch.setattr("dash.habits_edit.shutil.copy2", boom)
    with pytest.raises(HabitCompletionError, match="backup"):
        edit_habits_file(p, "Read", TODAY)
    assert p.read_text() == SAMPLE


def test_file_permissions_preserved(tmp_path):
    p = write(tmp_path)
    p.chmod(0o600)
    edit_habits_file(p, "Read", TODAY)
    assert p.stat().st_mode & 0o777 == 0o600


def test_widget_still_reads_the_edited_file(tmp_path):
    from dash.widgets.habits import HabitsWidget

    p = write(tmp_path)
    edit_habits_file(p, "Drink water", TODAY)
    data = HabitsWidget(today=lambda: TODAY).fetch({"path": str(p)})
    assert data["habits"][0] == {"name": "Drink water", "done_today": True, "streak": 1}
