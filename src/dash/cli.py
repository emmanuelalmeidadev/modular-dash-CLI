"""The `dash` command: single pass, fetch -> render -> exit. Also `dash habit done`."""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable, TextIO

from .cache import Cache
from .config import Config, ConfigError, load_config
from .habits_edit import HabitCompletionError, edit_habits_file, parse_day
from .registry import Registry
from .render_json import render_json
from .render_terminal import make_console, render_terminal
from .runner import run_widgets
from .widgets.github_tasks import GitHubTasksWidget
from .widgets.habits import HabitsWidget
from .widgets.weather import WeatherWidget


def default_registry() -> Registry:
    registry = Registry()
    for widget in (WeatherWidget(), GitHubTasksWidget(), HabitsWidget()):
        registry.register(widget)
    return registry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dash", description="Modular CLI personal dashboard")
    parser.add_argument("--json", action="store_true", help="print results as one JSON document")
    parser.add_argument("--refresh", action="store_true", help="bypass the cache")
    parser.add_argument("--config", type=Path, help="path to config file (default: platform config dir)")

    commands = parser.add_subparsers(dest="command", metavar="{habit}")
    habit = commands.add_parser("habit", help="work with your habits file")
    habit_commands = habit.add_subparsers(dest="habit_command", required=True, metavar="{done}")
    done = habit_commands.add_parser("done", help="record a habit as completed")
    done.add_argument("name", help="habit name (case-insensitive)")
    done.add_argument("--date", metavar="YYYY-MM-DD", help="day to record (default: today)")
    # SUPPRESS: a --config given before the subcommand must not be overwritten by this default
    done.add_argument("--config", type=Path, default=argparse.SUPPRESS, help="path to config file")
    return parser


def _habits_path(config: Config, config_hint: str) -> Path:
    for widget in config.widgets:
        if widget.id == "habits":
            raw = widget.options.get("path")
            if raw:
                return Path(str(raw)).expanduser()
            break
    raise ConfigError(f"'habit done' needs a habits widget with a 'path' option in {config_hint}")


def _habit_done(args: argparse.Namespace, now: datetime, stdout: TextIO, stderr: TextIO) -> int:
    try:
        config = load_config(args.config)
        path = _habits_path(config, str(args.config) if args.config else "your config file")
    except ConfigError as exc:
        print(f"dash: {exc}", file=stderr)
        return 2
    try:
        day = parse_day(args.date, now.date())
        result = edit_habits_file(path, args.name, day)
    except HabitCompletionError as exc:
        print(f"dash: {exc}", file=stderr)
        return 1
    verb = "Recorded" if result.added else "Already recorded"
    print(f"{verb}: {result.habit} done on {result.day.isoformat()}", file=stdout)
    return 0


def main(
    argv: list[str] | None = None,
    *,
    registry: Registry | None = None,
    cache: Cache | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    clock: Callable[[], datetime] | None = None,
) -> int:
    args = build_parser().parse_args(argv)
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr
    now = (clock or (lambda: datetime.now().astimezone()))()  # read once: header and JSON must agree

    if args.command == "habit":
        return _habit_done(args, now, stdout, stderr)

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"dash: {exc}", file=stderr)
        return 2

    results = run_widgets(config, registry or default_registry(), cache or Cache(), refresh=args.refresh)
    if args.json:
        print(render_json(results, now), file=stdout)
    else:
        render_terminal(results, make_console(stdout), now)
    return 0  # widgets may have failed individually; the dashboard itself was produced
