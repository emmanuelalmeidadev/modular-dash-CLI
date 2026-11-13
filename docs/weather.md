# Weather widget

Current temperature, conditions, and today's high/low for one location.
Uses the free Open-Meteo service; no API key or account is needed.

## Enable it

```toml
[[widgets]]
id = "weather"
ttl = 1800   # optional; seconds to cache results (default 1800)

[widgets.options]
location = "Lisbon"   # required
units = "metric"      # optional: "metric" (default) or "imperial"
```

## Retries

If a request fails because of a connection problem or a timeout, the widget
retries it once. All attempts together are limited to 8 seconds, so a bad
connection never makes `pdash` hang; it falls back to the last cached result
(marked stale, with the reason) when there is one. Unknown locations and error
responses from the service are not retried.

## Errors

- No `location` configured: the widget shows an error naming the option.
- Location not found, or the service is unreachable: the widget shows an
  error. If an older cached result exists it is shown marked as stale instead.
