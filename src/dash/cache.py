"""TTL disk cache: one JSON file per (widget id, options) entry, written atomically."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Callable

from platformdirs import user_cache_path


def default_cache_dir() -> Path:
    return user_cache_path("dash")


class Cache:
    def __init__(self, directory: Path | None = None, clock: Callable[[], float] = time.time):
        self.directory = directory or default_cache_dir()
        self._clock = clock

    def _path(self, widget_id: str, options: dict[str, Any]) -> Path:
        digest = hashlib.sha256(json.dumps(options, sort_keys=True, default=str).encode()).hexdigest()[:16]
        safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in widget_id)
        return self.directory / f"{safe_id}-{digest}.json"

    def get(self, widget_id: str, options: dict[str, Any]) -> tuple[dict[str, Any], float] | None:
        """Return (data, age_seconds) or None. Age is not checked against any TTL here."""
        try:
            entry = json.loads(self._path(widget_id, options).read_text(encoding="utf-8"))
            return entry["data"], max(0.0, self._clock() - float(entry["fetched_at"]))
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def put(self, widget_id: str, options: dict[str, Any], data: dict[str, Any]) -> None:
        path = self._path(widget_id, options)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump({"fetched_at": self._clock(), "data": data}, fh)
            os.replace(tmp, path)
        except OSError:
            pass  # a cache that cannot be written must never break the dashboard
