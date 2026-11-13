import json

from dash.result import WidgetResult


def roundtrip(result):
    return WidgetResult.from_dict(json.loads(json.dumps(result.to_dict())))


def test_ok_result_roundtrips():
    r = WidgetResult("weather", "Weather", "ok", data={"temp": 21.5, "days": [1, 2]})
    assert roundtrip(r) == r


def test_error_result_roundtrips():
    r = WidgetResult.failure("github", "Github", "rate limited")
    assert r.status == "error" and r.error == "rate limited"
    assert roundtrip(r) == r


def test_stale_result_roundtrips():
    r = WidgetResult("weather", "Weather", "ok", data={"temp": 1}, stale=True)
    assert roundtrip(r).stale is True


def test_serialized_form_has_no_presentation_fields():
    keys = set(WidgetResult("a", "A", "ok").to_dict())
    assert keys == {"id", "title", "status", "data", "error", "stale", "stale_reason", "stale_age_seconds"}


def test_stale_details_roundtrip():
    r = WidgetResult("g", "G", "ok", data={"a": 1}, stale=True, stale_reason="rate limit", stale_age_seconds=7200.0)
    again = roundtrip(r)
    assert again == r and again.stale_reason == "rate limit" and again.stale_age_seconds == 7200.0


def test_fresh_result_has_no_stale_details():
    d = WidgetResult("a", "A", "ok").to_dict()
    assert d["stale_reason"] is None and d["stale_age_seconds"] is None


def test_legacy_dict_without_stale_details_still_loads():
    legacy = {"id": "a", "title": "A", "status": "ok", "data": {}, "error": None, "stale": True}
    r = WidgetResult.from_dict(legacy)
    assert r.stale and r.stale_reason is None and r.stale_age_seconds is None
