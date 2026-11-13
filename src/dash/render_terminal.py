"""Terminal renderer: turns widget results into panels and tables. Knows nothing about sources."""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Callable, TextIO

from rich import box
from rich.console import Console, Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .config import APP_NAME
from .result import WidgetResult


def make_console(stream: TextIO) -> Console:
    """No escape codes unless stdout is a terminal and NO_COLOR is unset."""
    if os.environ.get("NO_COLOR"):
        return Console(file=stream, force_terminal=False, color_system=None, highlight=False)
    return Console(file=stream, highlight=False)


def _kv_table(rows: list[tuple[str, str]]) -> Table:
    table = Table.grid(padding=(0, 2))
    table.add_column(style="bold")
    table.add_column()
    for key, value in rows:
        table.add_row(key, value)
    return table


def _weather(data: dict[str, Any]) -> RenderableType:
    unit = "°F" if data.get("units") == "imperial" else "°C"
    return _kv_table([
        ("Location", str(data["location"])),
        ("Now", f"{data['temperature']}{unit}, {data['conditions']}"),
        ("Today", f"low {data['low']}{unit} / high {data['high']}{unit}"),
    ])


def _github_section(label: str, block: dict[str, Any]) -> RenderableType:
    header = Text(f"{label} ({block['total']})", style="bold")
    if not block["items"]:
        return Group(header, Text("  nothing pending", style="dim"))
    table = Table(box=box.SIMPLE_HEAD, show_header=False, pad_edge=False)
    table.add_column(style="cyan", no_wrap=True)
    table.add_column()
    for it in block["items"]:
        table.add_row(f"{it['repo']}#{it['number']}", it["title"])
    extra = block["total"] - len(block["items"])
    parts: list[RenderableType] = [header, table]
    if extra > 0:
        parts.append(Text(f"  ...and {extra} more", style="dim"))
    return Group(*parts)


def _github(data: dict[str, Any]) -> RenderableType:
    return Group(
        _github_section("Assigned issues", data["assigned_issues"]),
        Text(""),
        _github_section("Review requests", data["review_requests"]),
    )


def _habits(data: dict[str, Any]) -> RenderableType:
    if not data["habits"]:
        return Text("no habits defined", style="dim")
    table = Table(box=box.SIMPLE_HEAD)
    table.add_column("Habit")
    table.add_column("Today", justify="center")
    table.add_column("Streak", justify="right")
    for h in data["habits"]:
        mark = Text("done", style="green") if h["done_today"] else Text("todo", style="yellow")
        table.add_row(h["name"], mark, f"{h['streak']}d")
    return table


def _generic(data: dict[str, Any]) -> RenderableType:
    if not data:
        return Text("(no data)", style="dim")
    return _kv_table([(str(k), v if isinstance(v, str) else json.dumps(v)) for k, v in data.items()])


_RENDERERS: dict[str, Callable[[dict[str, Any]], RenderableType]] = {
    "weather": _weather,
    "github": _github,
    "habits": _habits,
}


def _body(result: WidgetResult) -> RenderableType:
    if result.status == "error":
        return Text(f"error: {result.error}", style="bold red")
    renderer = _RENDERERS.get(result.id, _generic)
    try:
        return renderer(result.data)
    except (KeyError, TypeError):
        return _generic(result.data)  # data shape unexpected: degrade, don't crash


def humanize_age(seconds: float) -> str:
    """Short human-readable age: 'just now', '5 min', '2 h', '3 d'."""
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{int(seconds // 60)} min"
    if seconds < 86400:
        return f"{int(seconds // 3600)} h"
    return f"{int(seconds // 86400)} d"


def _stale_label(result: WidgetResult) -> str:
    if result.stale_age_seconds is None:
        return "stale"
    age = humanize_age(result.stale_age_seconds)
    return "stale, just now" if age == "just now" else f"stale, {age} old"


def header_text(generated_at: datetime) -> str:
    return f"{APP_NAME} - {generated_at:%A %Y-%m-%d}, {generated_at:%H:%M}"


def _panel_body(result: WidgetResult) -> RenderableType:
    body = _body(result)
    if result.stale:
        reason = result.stale_reason or "unknown reason"
        return Group(body, Text(""), Text(f"Showing cached data. Refresh failed: {reason}", style="yellow"))
    return body


def render_terminal(results: list[WidgetResult], console: Console, generated_at: datetime) -> None:
    console.print(Text(header_text(generated_at), style="bold"))
    if not results:
        console.print("No widgets configured.")
        return
    for result in results:
        title = result.title + (f" ({_stale_label(result)})" if result.stale else "")
        style = "red" if result.status == "error" else ("yellow" if result.stale else "blue")
        console.print(Panel(_panel_body(result), title=title, title_align="left", border_style=style, expand=True))
