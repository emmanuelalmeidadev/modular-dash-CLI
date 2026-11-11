"""Widget interface and registry."""
from __future__ import annotations

from typing import Any, Protocol


class Widget(Protocol):
    """A widget fetches data and returns a JSON-serializable dict, or raises."""

    id: str
    title: str
    default_ttl: int  # seconds; 0 means "never cache" (e.g. local files)

    def fetch(self, options: dict[str, Any]) -> dict[str, Any]: ...


class Registry:
    def __init__(self) -> None:
        self._widgets: dict[str, Widget] = {}

    def register(self, widget: Widget) -> None:
        if widget.id in self._widgets:
            raise ValueError(f"widget id already registered: {widget.id}")
        self._widgets[widget.id] = widget

    def get(self, widget_id: str) -> Widget | None:
        return self._widgets.get(widget_id)

    def ids(self) -> list[str]:
        return list(self._widgets)
