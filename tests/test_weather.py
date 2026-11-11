import httpx
import pytest

from dash.widgets.weather import WeatherError, WeatherWidget

GEO = {"results": [{"name": "Lisbon", "country": "Portugal", "latitude": 38.7, "longitude": -9.1}]}
FORECAST = {
    "current": {"temperature_2m": 21.5, "weather_code": 2},
    "daily": {"temperature_2m_max": [24.0], "temperature_2m_min": [16.5]},
}


def widget(handler):
    return WeatherWidget(client=httpx.Client(transport=httpx.MockTransport(handler)))


def ok_handler(request):
    if "geocoding" in request.url.host:
        return httpx.Response(200, json=GEO)
    return httpx.Response(200, json=FORECAST)


def test_current_conditions_in_metric_by_default():
    seen = {}

    def handler(request):
        if "geocoding" not in request.url.host:
            seen.update(dict(request.url.params))
        return ok_handler(request)

    data = widget(handler).fetch({"location": "Lisbon"})
    assert data == {
        "location": "Lisbon, Portugal", "units": "metric", "temperature": 21.5,
        "conditions": "Partly cloudy", "high": 24.0, "low": 16.5,
    }
    assert seen["temperature_unit"] == "celsius"


def test_imperial_units_requested():
    seen = {}

    def handler(request):
        seen.update(dict(request.url.params))
        return ok_handler(request)

    data = widget(handler).fetch({"location": "Lisbon", "units": "imperial"})
    assert data["units"] == "imperial" and seen["temperature_unit"] == "fahrenheit"


@pytest.mark.parametrize("options", [{}, {"location": "  "}])
def test_location_required(options):
    with pytest.raises(WeatherError, match="location"):
        widget(ok_handler).fetch(options)


def test_invalid_units_rejected():
    with pytest.raises(WeatherError, match="units"):
        widget(ok_handler).fetch({"location": "x", "units": "kelvin"})


def test_unknown_location():
    w = widget(lambda r: httpx.Response(200, json={}))
    with pytest.raises(WeatherError, match="location not found"):
        w.fetch({"location": "Nowhereville"})


def test_service_unreachable():
    def handler(request):
        raise httpx.ConnectError("boom")

    with pytest.raises(WeatherError, match="unavailable"):
        widget(handler).fetch({"location": "Lisbon"})


def test_service_http_error():
    with pytest.raises(WeatherError, match="unavailable"):
        widget(lambda r: httpx.Response(503)).fetch({"location": "Lisbon"})


def test_unusable_response():
    def handler(request):
        if "geocoding" in request.url.host:
            return httpx.Response(200, json=GEO)
        return httpx.Response(200, json={"current": {}})

    with pytest.raises(WeatherError, match="unexpected"):
        widget(handler).fetch({"location": "Lisbon"})
