# Spec Delta

## ADDED Requirements

### Requirement: Stale results explain themselves
A result served as stale SHALL include the reason the fresh fetch failed and the age of the cached data in seconds. Results that are not stale SHALL carry neither value.

#### Scenario: Stale after a failed fetch
- **WHEN** a fetch fails with the message "rate limit exceeded" and a cached result 7200 seconds old is served
- **THEN** the result is marked stale with reason "rate limit exceeded" and age 7200 seconds

#### Scenario: Fresh result carries no stale details
- **WHEN** a widget returns freshly fetched or still-valid cached data
- **THEN** the result has no stale reason and no stale age
