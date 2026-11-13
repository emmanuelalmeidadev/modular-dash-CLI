"""The widget result model: plain data, no presentation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Status = Literal["ok", "error"]


@dataclass
class WidgetResult:
    id: str
    title: str
    status: Status
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    stale: bool = False
    stale_reason: str | None = None  # why the fresh fetch failed (stale results only)
    stale_age_seconds: float | None = None  # age of the cached data (stale results only)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "data": self.data,
            "error": self.error,
            "stale": self.stale,
            "stale_reason": self.stale_reason,
            "stale_age_seconds": self.stale_age_seconds,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "WidgetResult":
        return cls(
            id=raw["id"],
            title=raw["title"],
            status=raw["status"],
            data=raw.get("data", {}),
            error=raw.get("error"),
            stale=raw.get("stale", False),
            stale_reason=raw.get("stale_reason"),
            stale_age_seconds=raw.get("stale_age_seconds"),
        )

    @classmethod
    def failure(cls, id: str, title: str, message: str) -> "WidgetResult":
        return cls(id=id, title=title, status="error", error=message)
