# Spec Delta

## ADDED Requirements

### Requirement: Transient failures are retried once
When a weather request fails because of a connection error or a timeout, the widget SHALL retry that request once before reporting an error. Other failures, including unknown locations and error responses from the service, SHALL NOT be retried.

#### Scenario: Succeeds on retry
- **WHEN** the first request times out and the second succeeds
- **THEN** the widget returns an `ok` result with the weather data

#### Scenario: Fails twice
- **WHEN** both attempts fail with connection errors
- **THEN** the widget returns an `error` result stating the service is unavailable, subject to the stale-data rule

#### Scenario: Unknown location is not retried
- **WHEN** the service reports that the location does not exist
- **THEN** the widget returns an `error` result without making a second request
