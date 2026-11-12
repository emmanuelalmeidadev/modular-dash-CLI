"""JSON renderer: the widget result model, serialized and nothing else."""
from __future__ import annotations

import json
from datetime import datetime

from .result import WidgetResult


def render_json(results: list[WidgetResult], generated_at: datetime) -> str:
    document = {
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "widgets": [r.to_dict() for r in results],
    }
    return json.dumps(document, indent=2)
