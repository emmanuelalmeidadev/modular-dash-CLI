"""Habits widget: read-only view of a hand-maintained TOML file."""
from __future__ import annotations

import tomllib
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Callable


class HabitsError(Exception):
    pass


def _to_date(value: Any, habit: str) -> date:
    if isinstance(value, date):  # TOML native local date
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            pass
    raise HabitsError(f"habit '{habit}': invalid date {value!r} (use YYYY-MM-DD)")


def current_streak(days: set[date], today: date) -> int:
    """Consecutive completed days ending today, or yesterday if today isn't done yet."""
    cursor = today if today in days else today - timedelta(days=1)
    streak = 0
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


class HabitsWidget:
    id = "habits"
    title = "Habits"
    default_ttl = 0  # local file: always read fresh

    def __init__(self, today: Callable[[], date] = date.today):
        self._today = today

    def fetch(self, options: dict[str, Any]) -> dict[str, Any]:
        raw_path = options.get("path")
        if not raw_path:
            raise HabitsError("option 'path' is required (path to your habits TOML file)")
        path = Path(str(raw_path)).expanduser()
        try:
            parsed = tomllib.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise HabitsError(f"habits file not found: expected at {path}") from None
        except tomllib.TOMLDecodeError as exc:
            raise HabitsError(f"cannot parse habits file {path}: {exc}") from None
        except OSError as exc:
            raise HabitsError(f"cannot read habits file {path}: {exc}") from None

        today = self._today()
        habits = []
        for entry in parsed.get("habits", []):
            name = entry.get("name") if isinstance(entry, dict) else None
            if not isinstance(name, str):
                raise HabitsError(f"habits file {path}: every [[habits]] entry needs a string 'name'")
            days = {_to_date(d, name) for d in entry.get("done", [])}
            habits.append({"name": name, "done_today": today in days, "streak": current_streak(days, today)})
        return {"date": today.isoformat(), "habits": habits}
