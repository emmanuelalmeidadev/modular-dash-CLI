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

## Errors

- No `location` configured: the widget shows an error naming the option.
- Location not found, or the service is unreachable: the widget shows an
  error. If an older cached result exists it is shown marked as stale instead.
