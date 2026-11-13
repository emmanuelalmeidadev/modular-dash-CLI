import json
from datetime import datetime, timedelta, timezone

from dash.render_json import render_json
from dash.result import WidgetResult

NOW = datetime(2026, 11, 12, 14, 3, 7, tzinfo=timezone(timedelta(hours=-7)))


def test_single_parseable_document_one_entry_per_widget():
    results = [
        WidgetResult("weather", "Weather", "ok", data={"temperature": 20}),
        WidgetResult.failure("github", "GitHub", "rate limit"),
        WidgetResult("habits", "Habits", "ok", data={"habits": []}, stale=True),
    ]
    doc = json.loads(render_json(results, NOW))
    assert [w["id"] for w in doc["widgets"]] == ["weather", "github", "habits"]
    assert doc["widgets"][1]["status"] == "error" and doc["widgets"][1]["error"] == "rate limit"
    assert doc["widgets"][2]["stale"] is True
    assert doc["widgets"][0]["data"] == {"temperature": 20}


def test_generated_at_is_iso_8601_with_offset():
    doc = json.loads(render_json([], NOW))
    assert doc["generated_at"] == "2026-11-12T14:03:07-07:00"
    assert datetime.fromisoformat(doc["generated_at"]) == NOW


def test_stale_entry_has_reason_and_age_and_others_do_not():
    stale = WidgetResult("g", "G", "ok", data={}, stale=True, stale_reason="rate limit", stale_age_seconds=7200.0)
    fresh = WidgetResult("w", "W", "ok", data={})
    doc = json.loads(render_json([stale, fresh], NOW))
    assert doc["widgets"][0]["stale_reason"] == "rate limit" and doc["widgets"][0]["stale_age_seconds"] == 7200.0
    assert doc["widgets"][1]["stale"] is False
    assert doc["widgets"][1]["stale_reason"] is None and doc["widgets"][1]["stale_age_seconds"] is None


def test_no_escape_codes():
    assert "\x1b" not in render_json([WidgetResult("a", "A", "ok")], NOW)
