"""Weather widget: current conditions and today's high/low (Open-Meteo, no API key)."""
from __future__ import annotations

import time
from typing import Any, Callable

import httpx

# Total time budget for ALL attempts. It stays below the framework's default 10 s widget timeout,
# so a failure still raises (and the stale-data fallback applies) instead of being cut off.
TOTAL_BUDGET = 8.0
ATTEMPT_TIMEOUT = 4.0
MIN_TIME_FOR_RETRY = 1.0
# Only connection-level problems are worth one retry; HTTP error responses are not.
_TRANSIENT = (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError)

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather interpretation codes -> short summary
_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Rime fog",
    51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
    56: "Freezing drizzle", 57: "Freezing drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain",
    66: "Freezing rain", 67: "Freezing rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow", 77: "Snow grains",
    80: "Rain showers", 81: "Rain showers", 82: "Violent rain showers",
    85: "Snow showers", 86: "Snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with hail",
}


class WeatherError(Exception):
    pass


class WeatherWidget:
    id = "weather"
    title = "Weather"
    default_ttl = 1800

    def __init__(self, client: httpx.Client | None = None, clock: Callable[[], float] = time.monotonic):
        self._client = client
        self._clock = clock

    def _get(self, client: httpx.Client, url: str, params: dict[str, Any], deadline: float) -> httpx.Response:
        """GET with at most one retry on a transient failure, inside the overall deadline."""
        attempt = 0
        while True:
            attempt += 1
            timeout = max(0.1, min(ATTEMPT_TIMEOUT, deadline - self._clock()))
            try:
                response = client.get(url, params=params, timeout=timeout)
            except _TRANSIENT:
                if attempt >= 2 or deadline - self._clock() < MIN_TIME_FOR_RETRY:
                    raise
                continue
            response.raise_for_status()
            return response

    def fetch(self, options: dict[str, Any]) -> dict[str, Any]:
        location = options.get("location")
        if not location or not str(location).strip():
            raise WeatherError("option 'location' is required (for example location = \"Lisbon\")")
        units = str(options.get("units", "metric")).lower()
        if units not in ("metric", "imperial"):
            raise WeatherError("option 'units' must be 'metric' or 'imperial'")

        client = self._client or httpx.Client(timeout=ATTEMPT_TIMEOUT)
        deadline = self._clock() + TOTAL_BUDGET
        try:
            place = self._geocode(client, str(location).strip(), deadline)
            forecast = self._forecast(client, place, units, deadline)
        except httpx.HTTPError as exc:
            raise WeatherError(f"weather service unavailable: {exc.__class__.__name__}") from exc
        finally:
            if self._client is None:
                client.close()

        try:
            current, daily = forecast["current"], forecast["daily"]
            return {
                "location": place["label"],
                "units": units,
                "temperature": current["temperature_2m"],
                "conditions": _CODES.get(current.get("weather_code"), "Unknown"),
                "high": daily["temperature_2m_max"][0],
                "low": daily["temperature_2m_min"][0],
            }
        except (KeyError, IndexError, TypeError):
            raise WeatherError("weather service returned an unexpected response") from None

    def _geocode(self, client: httpx.Client, name: str, deadline: float) -> dict[str, Any]:
        resp = self._get(client, GEOCODE_URL, {"name": name, "count": 1}, deadline)
        try:
            hit = resp.json()["results"][0]
            label = ", ".join(p for p in (hit["name"], hit.get("country")) if p)
            return {"lat": hit["latitude"], "lon": hit["longitude"], "label": label}
        except (KeyError, IndexError, TypeError, ValueError):
            raise WeatherError(f"location not found: {name}") from None

    def _forecast(self, client: httpx.Client, place: dict[str, Any], units: str, deadline: float) -> dict[str, Any]:
        params = {
            "latitude": place["lat"],
            "longitude": place["lon"],
            "current": "temperature_2m,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min",
            "forecast_days": 1,
            "timezone": "auto",
            "temperature_unit": "fahrenheit" if units == "imperial" else "celsius",
        }
        resp = self._get(client, FORECAST_URL, params, deadline)
        try:
            return resp.json()
        except ValueError:
            raise WeatherError("weather service returned an unexpected response") from None
