"""JSON renderer: the widget result model, serialized and nothing else."""
from __future__ import annotations

import json

from .result import WidgetResult


def render_json(results: list[WidgetResult]) -> str:
    return json.dumps({"widgets": [r.to_dict() for r in results]}, indent=2)
