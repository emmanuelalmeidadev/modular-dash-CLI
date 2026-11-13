"""Run widgets concurrently with timeouts, failure isolation and caching."""
from __future__ import annotations

import threading
import time

from .cache import Cache
from .config import Config, WidgetConfig
from .registry import Registry, Widget
from .result import WidgetResult


def _fetch_with_cache(widget: Widget, wc: WidgetConfig, cache: Cache, refresh: bool) -> WidgetResult:
    ttl = wc.ttl if wc.ttl is not None else widget.default_ttl
    cached = cache.get(widget.id, wc.options) if ttl > 0 else None
    if cached and not refresh and cached[1] < ttl:
        return WidgetResult(widget.id, widget.title, "ok", data=cached[0])
    try:
        data = widget.fetch(wc.options)
    except Exception as exc:  # isolation: any widget failure becomes an error result
        message = str(exc) or exc.__class__.__name__
        if cached:
            return WidgetResult(
                widget.id, widget.title, "ok", data=cached[0],
                stale=True, stale_reason=message, stale_age_seconds=cached[1],
            )
        return WidgetResult.failure(widget.id, widget.title, message)
    if ttl > 0:
        cache.put(widget.id, wc.options, data)
    return WidgetResult(widget.id, widget.title, "ok", data=data)


def run_widgets(config: Config, registry: Registry, cache: Cache, refresh: bool = False) -> list[WidgetResult]:
    """Fetch every configured widget concurrently; results keep config order."""
    slots: list[WidgetResult | None] = [None] * len(config.widgets)
    threads: list[tuple[int, threading.Thread]] = []

    abandoned: set[int] = set()

    def work(index: int, widget: Widget, wc: WidgetConfig) -> None:
        result = _fetch_with_cache(widget, wc, cache, refresh)
        if index not in abandoned:  # a late finisher must not overwrite its timeout result
            slots[index] = result

    for index, wc in enumerate(config.widgets):
        widget = registry.get(wc.id)
        if widget is None:
            slots[index] = WidgetResult.failure(wc.id, wc.id, f"unknown widget '{wc.id}'")
            continue
        # daemon threads: a hung widget must not keep the process alive after timeout
        thread = threading.Thread(target=work, args=(index, widget, wc), daemon=True)
        thread.start()
        threads.append((index, thread))

    deadline = time.monotonic() + config.timeout
    for index, thread in threads:
        thread.join(max(0.0, deadline - time.monotonic()))
        if thread.is_alive() and slots[index] is None:
            abandoned.add(index)
            wc = config.widgets[index]
            widget = registry.get(wc.id)
            title = widget.title if widget else wc.id
            slots[index] = WidgetResult.failure(wc.id, title, f"timed out after {config.timeout:g}s")
    return [s for s in slots if s is not None]
