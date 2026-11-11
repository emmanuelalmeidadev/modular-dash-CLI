from __future__ import annotations

from typing import Any, Callable

import pytest

from dash.cache import Cache


class FakeWidget:
    def __init__(self, id: str, fetch: Callable[[dict[str, Any]], dict[str, Any]] | None = None, ttl: int = 60):
        self.id = id
        self.title = id.title()
        self.default_ttl = ttl
        self.calls = 0
        self._fetch = fetch or (lambda options: {"value": 1})

    def fetch(self, options: dict[str, Any]) -> dict[str, Any]:
        self.calls += 1
        return self._fetch(options)


@pytest.fixture
def cache(tmp_path):
    return Cache(tmp_path / "cache")


@pytest.fixture
def fake_widget():
    return FakeWidget
