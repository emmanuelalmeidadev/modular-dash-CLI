"""The `dash` command: single pass, fetch -> render -> exit."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TextIO

from .cache import Cache
from .config import ConfigError, load_config
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
    return parser


def main(
    argv: list[str] | None = None,
    *,
    registry: Registry | None = None,
    cache: Cache | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    args = build_parser().parse_args(argv)
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"dash: {exc}", file=stderr)
        return 2

    results = run_widgets(config, registry or default_registry(), cache or Cache(), refresh=args.refresh)
    if args.json:
        print(render_json(results), file=stdout)
    else:
        render_terminal(results, make_console(stdout))
    return 0  # widgets may have failed individually; the dashboard itself was produced
