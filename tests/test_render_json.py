import json

from dash.render_json import render_json
from dash.result import WidgetResult


def test_single_parseable_document_one_entry_per_widget():
    results = [
        WidgetResult("weather", "Weather", "ok", data={"temperature": 20}),
        WidgetResult.failure("github", "GitHub", "rate limit"),
        WidgetResult("habits", "Habits", "ok", data={"habits": []}, stale=True),
    ]
    doc = json.loads(render_json(results))
    assert [w["id"] for w in doc["widgets"]] == ["weather", "github", "habits"]
    assert doc["widgets"][1]["status"] == "error" and doc["widgets"][1]["error"] == "rate limit"
    assert doc["widgets"][2]["stale"] is True
    assert doc["widgets"][0]["data"] == {"temperature": 20}


def test_no_escape_codes():
    assert "\x1b" not in render_json([WidgetResult("a", "A", "ok")])
