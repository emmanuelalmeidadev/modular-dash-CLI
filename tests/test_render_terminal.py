import io
from datetime import datetime

import pytest

from dash.render_terminal import header_text, humanize_age, make_console, render_terminal
from dash.result import WidgetResult

WEATHER = WidgetResult("weather", "Weather", "ok", data={
    "location": "Lisbon, Portugal", "units": "metric", "temperature": 21.5,
    "conditions": "Partly cloudy", "high": 24.0, "low": 16.5})
GITHUB = WidgetResult("github", "GitHub", "ok", data={
    "assigned_issues": {"total": 7, "items": [{"repo": "o/r", "number": 3, "title": "Fix bug", "url": "u"}]},
    "review_requests": {"total": 0, "items": []}})
HABITS = WidgetResult("habits", "Habits", "ok", data={"date": "2026-11-11", "habits": [
    {"name": "Read", "done_today": True, "streak": 3}, {"name": "Run", "done_today": False, "streak": 0}]})


NOW = datetime(2026, 11, 12, 14, 3)  # a Thursday


def render(results, monkeypatch, no_color=True):
    if no_color:
        monkeypatch.setenv("NO_COLOR", "1")
    else:
        monkeypatch.delenv("NO_COLOR", raising=False)
    buf = io.StringIO()
    render_terminal(results, make_console(buf), NOW)
    return buf.getvalue()


def test_weather_section(monkeypatch):
    out = render([WEATHER], monkeypatch)
    assert "Weather" in out and "Lisbon, Portugal" in out and "21.5°C" in out and "Partly cloudy" in out


def test_github_section_shows_totals_and_overflow(monkeypatch):
    out = render([GITHUB], monkeypatch)
    assert "Assigned issues (7)" in out and "o/r#3" in out and "...and 6 more" in out
    assert "nothing pending" in out


def test_habits_section(monkeypatch):
    out = render([HABITS], monkeypatch)
    assert "Read" in out and "done" in out and "3d" in out and "todo" in out


def test_error_widget_inline_and_others_render(monkeypatch):
    out = render([WidgetResult.failure("github", "GitHub", "rate limit exceeded"), WEATHER], monkeypatch)
    assert "error: rate limit exceeded" in out and "Lisbon" in out


def test_stale_marked(monkeypatch):
    stale = WidgetResult("weather", "Weather", "ok", data=WEATHER.data, stale=True)
    assert "(stale)" in render([stale], monkeypatch)


@pytest.mark.parametrize("age, text", [(30, "just now"), (300, "5 min"), (7200, "2 h"), (3 * 86400 + 5, "3 d")])
def test_stale_panel_shows_age_and_reason(monkeypatch, age, text):
    stale = WidgetResult("weather", "Weather", "ok", data=WEATHER.data, stale=True,
                         stale_reason="rate limit exceeded", stale_age_seconds=age)
    out = render([stale], monkeypatch)
    assert text in out and "Refresh failed: rate limit exceeded" in out and "stale" in out


def test_stale_panel_without_details_still_renders(monkeypatch):
    stale = WidgetResult("weather", "Weather", "ok", data=WEATHER.data, stale=True)
    out = render([stale], monkeypatch)
    assert "unknown reason" in out and "Lisbon" in out


def test_header_shows_weekday_date_and_time(monkeypatch):
    assert header_text(NOW) == "pdash - Thursday 2026-11-12, 14:03"
    assert render([WEATHER], monkeypatch).splitlines()[0].strip() == "pdash - Thursday 2026-11-12, 14:03"


def test_header_printed_even_with_no_widgets(monkeypatch):
    out = render([], monkeypatch)
    assert "Thursday 2026-11-12" in out and "No widgets configured" in out


def test_humanize_age_boundaries():
    assert [humanize_age(s) for s in (0, 59, 60, 3599, 3600, 86399, 86400)] == [
        "just now", "just now", "1 min", "59 min", "1 h", "23 h", "1 d"]


def test_unknown_widget_uses_generic_fallback(monkeypatch):
    out = render([WidgetResult("custom", "Custom", "ok", data={"answer": 42, "list": [1, 2]})], monkeypatch)
    assert "answer" in out and "42" in out and "[1, 2]" in out


def test_malformed_data_degrades_instead_of_crashing(monkeypatch):
    out = render([WidgetResult("weather", "Weather", "ok", data={"unexpected": True})], monkeypatch)
    assert "unexpected" in out


def test_no_escape_codes_when_not_a_terminal(monkeypatch):
    stale = WidgetResult("weather", "Weather", "ok", data=WEATHER.data, stale=True, stale_reason="x", stale_age_seconds=9000)
    assert "\x1b" not in render([WEATHER, GITHUB, HABITS, stale], monkeypatch, no_color=False)


def test_no_escape_codes_with_no_color(monkeypatch):
    assert "\x1b" not in render([WEATHER, GITHUB, HABITS], monkeypatch, no_color=True)


def test_no_widgets_message(monkeypatch):
    assert "No widgets configured" in render([], monkeypatch)
