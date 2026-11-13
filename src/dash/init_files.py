"""First-run setup: starter config and habits files, created without ever overwriting."""
from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

import tomlkit

DEFAULT_HABITS_PATH = "~/habits.toml"
PLACEHOLDER_LOCATION = "London"


class SetupError(Exception):
    """A file could not be created; message names the path and the cause."""


@dataclass
class Outcome:
    path: Path
    created: bool  # False means it already existed and was left untouched


_CONFIG_TEMPLATE = '''# pdash config. Run `pdash` to show the dashboard.
timeout = 10   # seconds to wait for any single widget

[[widgets]]
id = "weather"
[widgets.options]
location = {location}{location_comment}
units = "metric"   # or "imperial"

[[widgets]]
id = "github"
[widgets.options]
limit = 5
# The token is read from the GITHUB_TOKEN environment variable. Alternatively,
# uncomment this to fetch it from a command (the config file can run commands,
# so keep it private):
# token_cmd = "gh auth token"

[[widgets]]
id = "habits"
[widgets.options]
path = "{habits_path}"
'''

STARTER_HABITS = '''# Habits tracked by pdash. Mark one done with:  pdash habit done "Read"
# Or add a date to a habit's `done` list by hand.

[[habits]]
name = "Drink water"
done = []

[[habits]]
name = "Read"
done = []

[[habits]]
name = "Exercise"
done = []
'''


def starter_config(location: str | None = None, habits_path: str = DEFAULT_HABITS_PATH) -> str:
    """Starter config text. A custom location is written as a safely quoted TOML string."""
    if location is None:
        quoted, comment = tomlkit.string(PLACEHOLDER_LOCATION).as_string(), "   # change this to your city"
    else:
        quoted, comment = tomlkit.string(location).as_string(), ""
    return _CONFIG_TEMPLATE.format(location=quoted, location_comment=comment, habits_path=habits_path)


def create_if_absent(path: Path, content: str) -> Outcome:
    """Create `path` with `content` unless it exists. Never overwrites; never leaves a partial file.

    The content is written to a temporary file first and then linked into place; the link
    fails if the destination exists, which makes create-if-absent atomic.
    """
    tmp_name = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
        try:
            fh = os.fdopen(fd, "w", encoding="utf-8")
        except BaseException:
            os.close(fd)
            raise
        with fh:
            fh.write(content)
        try:
            os.link(tmp_name, path)
        except FileExistsError:
            return Outcome(path, created=False)
        return Outcome(path, created=True)
    except OSError as exc:
        raise SetupError(f"cannot create {path}: {exc.strerror or exc}") from None
    finally:
        if tmp_name and os.path.exists(tmp_name):
            os.unlink(tmp_name)


def run_init(config_path: Path, habits_path: Path, location: str | None = None,
             habits_ref: str = DEFAULT_HABITS_PATH) -> list[Outcome]:
    """Create the starter config and habits file; each is skipped if it already exists."""
    return [
        create_if_absent(config_path, starter_config(location, habits_ref)),
        create_if_absent(habits_path, STARTER_HABITS),
    ]
