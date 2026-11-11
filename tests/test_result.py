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
    assert keys == {"id", "title", "status", "data", "error", "stale"}
