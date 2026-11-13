# widget-framework Specification

## Purpose

Defines how dashboard widgets are registered, configured, fetched and cached, so that new widgets can be added without changing rendering or configuration handling, and one failing widget never breaks the dashboard.

## Requirements

### Requirement: Widgets return a serializable result
Each widget SHALL produce a result consisting of its id, a title, a status of `ok` or `error`, and a data payload that is representable as JSON. A widget result SHALL NOT contain presentation (colors, layout, escape codes).

#### Scenario: Successful widget result
- **WHEN** a widget fetches its data successfully
- **THEN** its result has status `ok` and a JSON-representable payload

### Requirement: Widgets are selected and ordered by configuration
The system SHALL read a single user config file listing the enabled widgets, their display order, and per-widget options. Widgets not listed SHALL NOT run.

#### Scenario: Only listed widgets run
- **WHEN** the config lists `weather` then `habits`
- **THEN** only those two widgets are fetched and results appear in that order

#### Scenario: Unknown widget id
- **WHEN** the config lists an id that no registered widget provides
- **THEN** the dashboard reports an error result for that id and still renders the others

#### Scenario: Missing config file
- **WHEN** no config file exists
- **THEN** the system exits with a message stating where the config file is expected, and does not crash

### Requirement: Widgets are fetched concurrently
The system SHALL fetch all enabled widgets concurrently so total latency is bounded by the slowest widget rather than the sum.

#### Scenario: Slow widget does not serialize others
- **WHEN** two widgets each take 2 seconds to fetch
- **THEN** the full run completes in under 4 seconds

### Requirement: Widget failures are isolated
A failure or timeout in one widget SHALL produce an `error` result with a human-readable message for that widget only. Other widgets SHALL complete normally.

#### Scenario: One widget raises an error
- **WHEN** the GitHub widget fails with a network error
- **THEN** its result has status `error` with a message, and the weather and habits widgets still return `ok`

#### Scenario: Widget exceeds timeout
- **WHEN** a widget does not finish within the configured timeout
- **THEN** it is reported as an `error` result stating that it timed out

### Requirement: Results are cached with a time-to-live
For widgets that fetch from external services, the system SHALL cache successful results on disk and reuse them until their TTL expires. A `--refresh` option SHALL bypass the cache. Error results SHALL NOT be cached.

#### Scenario: Cache hit
- **WHEN** a widget's cached result is younger than its TTL
- **THEN** the system returns it without performing the external request

#### Scenario: Cache expired or bypassed
- **WHEN** the cached result is older than its TTL, or the user passes `--refresh`
- **THEN** the system fetches fresh data and updates the cache

#### Scenario: Stale data on failure
- **WHEN** a fetch fails and an expired cached result exists
- **THEN** the widget returns the cached data marked as stale instead of a bare error

### Requirement: Stale results explain themselves
A result served as stale SHALL include the reason the fresh fetch failed and the age of the cached data in seconds. Results that are not stale SHALL carry neither value.

#### Scenario: Stale after a failed fetch
- **WHEN** a fetch fails with the message "rate limit exceeded" and a cached result 7200 seconds old is served
- **THEN** the result is marked stale with reason "rate limit exceeded" and age 7200 seconds

#### Scenario: Fresh result carries no stale details
- **WHEN** a widget returns freshly fetched or still-valid cached data
- **THEN** the result has no stale reason and no stale age
