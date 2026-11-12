"""Recording habit completions. The only code that ever writes the habits file."""
from __future__ import annotations

import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import tomlkit
from tomlkit.exceptions import TOMLKitError

from .widgets.habits import HabitsError, to_date

_ISO_DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class HabitCompletionError(Exception):
    """Raised for any request that must not change the file; message is user-facing."""


@dataclass
class Completion:
    habit: str
    day: date
    added: bool  # False when the date was already recorded


def parse_day(arg: str | None, today: date) -> date:
    """Validate the --date argument (None means today). Rejects bad formats and future dates."""
    if arg is None:
        return today
    if not _ISO_DAY.match(arg):
        raise HabitCompletionError(f"invalid date {arg!r}: expected YYYY-MM-DD")
    try:
        day = date.fromisoformat(arg)
    except ValueError:
        raise HabitCompletionError(f"invalid date {arg!r}: not a real calendar date") from None
    if day > today:
        raise HabitCompletionError(f"date {arg} is in the future (today is {today.isoformat()})")
    return day


def _habit_tables(doc: Any, where: str) -> list[Any]:
    habits = doc.get("habits")
    if not isinstance(habits, list) or not all(hasattr(h, "get") and isinstance(h.get("name"), str) for h in habits):
        raise HabitCompletionError(f"{where} does not match the documented format: expected [[habits]] entries with a 'name'")
    return list(habits)


def complete(doc: Any, name: str, day: date, where: str = "habits file") -> Completion:
    """Add `day` to the named habit in a parsed document. Pure: touches no files."""
    tables = _habit_tables(doc, where)
    wanted = name.strip().casefold()
    matches = [t for t in tables if t["name"].strip().casefold() == wanted]
    if not matches:
        available = ", ".join(repr(t["name"]) for t in tables) or "(none defined)"
        raise HabitCompletionError(f"no habit named {name!r}. Available habits: {available}")
    if len(matches) > 1:
        raise HabitCompletionError(f"habit name {name!r} is ambiguous: {len(matches)} habits match")
    table = matches[0]

    try:
        existing = [to_date(d, table["name"]) for d in table.get("done", [])]
    except HabitsError as exc:
        raise HabitCompletionError(str(exc)) from None
    if day in existing:
        return Completion(table["name"], day, added=False)

    if "done" not in table:
        table["done"] = tomlkit.array()
    done = table["done"]
    native = bool(done) and all(isinstance(d, date) for d in done)  # follow the file's existing style
    done.append(day if native else day.isoformat())
    return Completion(table["name"], day, added=True)


def edit_habits_file(path: Path, name: str, day: date) -> Completion:
    """Record a completion in the file: validate first, back up, then replace atomically."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise HabitCompletionError(f"habits file not found: expected at {path} (nothing was created)") from None
    except OSError as exc:
        raise HabitCompletionError(f"cannot read habits file {path}: {exc}") from None
    try:
        doc = tomlkit.parse(text)
    except TOMLKitError as exc:
        raise HabitCompletionError(f"cannot parse habits file {path}: {exc}") from None

    result = complete(doc, name, day, where=str(path))  # all validation happens before any write
    if not result.added:
        return result  # idempotent: no backup, no rewrite

    backup = path.with_name(path.name + ".bak")
    try:
        shutil.copy2(path, backup)
    except OSError as exc:
        raise HabitCompletionError(f"could not write backup {backup}: {exc}; habits file left unchanged") from None

    tmp_name = None
    try:
        fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(tomlkit.dumps(doc))
        shutil.copymode(path, tmp_name)
        os.replace(tmp_name, path)
    except OSError as exc:
        if tmp_name and os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise HabitCompletionError(f"could not write {path}: {exc}; habits file left unchanged") from None
    return result
