import httpx
import pytest

from dash.cache import Cache
from dash.config import Config, WidgetConfig
from dash.registry import Registry
from dash.runner import run_widgets
from dash.widgets.weather import WeatherError, WeatherWidget

GEO = {"results": [{"name": "Lisbon", "country": "Portugal", "latitude": 38.7, "longitude": -9.1}]}
FORECAST = {"current": {"temperature_2m": 21.5, "weather_code": 2},
            "daily": {"temperature_2m_max": [24.0], "temperature_2m_min": [16.5]}}


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def widget(handler, clock=None):
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return WeatherWidget(client=client, clock=clock or FakeClock())


def good(request):
    return httpx.Response(200, json=GEO if "geocoding" in request.url.host else FORECAST)


def test_succeeds_on_retry_after_a_timeout():
    calls = []

    def handler(request):
        calls.append(request.url.host)
        if len(calls) == 1:
            raise httpx.ConnectTimeout("slow")
        return good(request)

    data = widget(handler).fetch({"location": "Lisbon"})
    assert data["temperature"] == 21.5
    assert len(calls) == 3  # geocode twice (one retry) + forecast once


@pytest.mark.parametrize("exc", [httpx.ConnectError("x"), httpx.ReadTimeout("x"), httpx.ReadError("x")])
def test_each_transient_error_type_is_retried_once(exc):
    calls = []

    def handler(request):
        calls.append(1)
        raise exc

    with pytest.raises(WeatherError, match="unavailable"):
        widget(handler).fetch({"location": "Lisbon"})
    assert len(calls) == 2  # first attempt + exactly one retry


def test_unknown_location_is_not_retried():
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(200, json={})

    with pytest.raises(WeatherError, match="location not found"):
        widget(handler).fetch({"location": "Nowhere"})
    assert len(calls) == 1


@pytest.mark.parametrize("status", [429, 500, 503])
def test_error_responses_are_not_retried(status):
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(status)

    with pytest.raises(WeatherError, match="unavailable"):
        widget(handler).fetch({"location": "Lisbon"})
    assert len(calls) == 1


def test_no_retry_when_too_little_budget_remains():
    clock = FakeClock()
    calls = []

    def handler(request):
        calls.append(1)
        clock.now += 7.5  # first attempt eats nearly the whole 8 s budget
        raise httpx.ConnectTimeout("slow")

    with pytest.raises(WeatherError, match="unavailable"):
        widget(handler, clock).fetch({"location": "Lisbon"})
    assert len(calls) == 1


def test_total_time_never_exceeds_the_budget():
    clock = FakeClock()
    timeouts = []

    def handler(request):
        timeouts.append(request.extensions["timeout"]["read"])
        clock.now += request.extensions["timeout"]["read"]  # each attempt uses its whole timeout
        raise httpx.ReadTimeout("slow")

    with pytest.raises(WeatherError):
        widget(handler, clock).fetch({"location": "Lisbon"})
    assert clock.now <= 8.0 + 1e-9
    assert all(t <= 4.0 for t in timeouts) and len(timeouts) == 2


def test_failure_after_retries_still_falls_back_to_stale_data(tmp_path):
    clock = FakeClock()
    cache_clock = FakeClock()
    cache = Cache(tmp_path / "c", clock=cache_clock)
    state = {"down": False}

    def handler(request):
        if state["down"]:
            raise httpx.ConnectError("no route")
        return good(request)

    reg = Registry()
    reg.register(widget(handler, clock))
    cfg = Config([WidgetConfig("weather", {"location": "Lisbon"})], 10.0)
    first = run_widgets(cfg, reg, cache)[0]
    assert first.status == "ok" and not first.stale
    cache_clock.now += 4000  # past the 30 minute TTL
    state["down"] = True
    again = run_widgets(cfg, reg, cache)[0]
    assert again.status == "ok" and again.stale and again.data["temperature"] == 21.5
    assert "unavailable" in again.stale_reason and again.stale_age_seconds == 4000
