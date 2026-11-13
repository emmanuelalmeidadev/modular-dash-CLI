"""Config loading (TOML): which widgets run, in what order, with which options."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from platformdirs import user_config_path

APP_NAME = "pdash"  # command name; also names the config and cache directories
DEFAULT_TIMEOUT = 10.0


class ConfigError(Exception):
    """Raised when the config cannot be used; message is user-facing."""


@dataclass
class WidgetConfig:
    id: str
    options: dict[str, Any] = field(default_factory=dict)
    ttl: int | None = None  # overrides the widget's default TTL


@dataclass
class Config:
    widgets: list[WidgetConfig]
    timeout: float = DEFAULT_TIMEOUT


def default_config_path() -> Path:
    return user_config_path(APP_NAME) / "config.toml"


def load_config(path: Path | None = None) -> Config:
    path = path or default_config_path()
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ConfigError(f"config file not found: expected at {path}") from None
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"invalid config {path}: {exc}") from None
    except OSError as exc:
        raise ConfigError(f"cannot read config {path}: {exc}") from None

    entries = raw.get("widgets", [])
    if not isinstance(entries, list):
        raise ConfigError(f"invalid config {path}: 'widgets' must be an array of tables")
    widgets: list[WidgetConfig] = []
    for i, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
            raise ConfigError(f"invalid config {path}: widgets[{i}] needs a string 'id'")
        options = entry.get("options", {})
        ttl = entry.get("ttl")
        if not isinstance(options, dict):
            raise ConfigError(f"invalid config {path}: widgets[{i}].options must be a table")
        if ttl is not None and (not isinstance(ttl, int) or isinstance(ttl, bool) or ttl < 0):
            raise ConfigError(f"invalid config {path}: widgets[{i}].ttl must be a non-negative integer")
        widgets.append(WidgetConfig(id=entry["id"], options=options, ttl=ttl))

    timeout = raw.get("timeout", DEFAULT_TIMEOUT)
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
        raise ConfigError(f"invalid config {path}: 'timeout' must be a positive number")
    return Config(widgets=widgets, timeout=float(timeout))
