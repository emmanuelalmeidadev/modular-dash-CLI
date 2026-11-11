# weather-widget Specification

## Purpose

Shows current weather conditions and a short forecast for a user-configured location, using a public weather service that requires no API key.

## Requirements

### Requirement: Weather for a configured location
The weather widget SHALL report current temperature, a conditions summary, and today's high and low for the location given in its options. Units (metric or imperial) SHALL be configurable and default to metric.

#### Scenario: Current conditions shown
- **WHEN** the widget is enabled with a valid location
- **THEN** its `ok` result contains temperature, conditions, high and low in the configured units

### Requirement: Location is required
The widget SHALL return an `error` result naming the missing option when no location is configured.

#### Scenario: No location configured
- **WHEN** the weather widget is enabled without a location option
- **THEN** its result has status `error` and the message states that `location` is required

### Requirement: Weather service unavailable
If the weather service cannot be reached or returns an unusable response, the widget SHALL return an `error` result, subject to the stale-data rule of the widget framework.

#### Scenario: Service unreachable
- **WHEN** the weather request fails and no cached data exists
- **THEN** the widget result has status `error` with a readable message
