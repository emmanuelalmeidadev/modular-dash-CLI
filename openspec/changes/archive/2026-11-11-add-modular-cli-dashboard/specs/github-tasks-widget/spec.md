# Spec Delta

## Purpose

Surfaces the GitHub work that currently needs the user's attention: open issues assigned to them and pull requests awaiting their review.

## ADDED Requirements

### Requirement: Assigned issues and review requests
The widget SHALL list open issues assigned to the authenticated user and open pull requests requesting their review. Each item SHALL include repository, number, title, and URL. The number of items per list SHALL be limited by a configurable maximum, defaulting to 5, and the total count SHALL be reported.

#### Scenario: Items listed
- **WHEN** the user has 8 assigned issues and the maximum is 5
- **THEN** the result lists 5 issues and reports a total of 8

#### Scenario: Nothing pending
- **WHEN** the user has no assigned issues and no review requests
- **THEN** the result is `ok` with empty lists and zero totals

### Requirement: Token from the environment
The widget SHALL authenticate using a token read from an environment variable and SHALL NOT read it from the config file or write it to the cache, output, or logs.

#### Scenario: Token missing
- **WHEN** the token environment variable is unset
- **THEN** the widget returns an `error` result explaining which variable to set

#### Scenario: Token never persisted
- **WHEN** the widget runs successfully with a token
- **THEN** neither the cache files nor the output contain the token value

### Requirement: Rate limits and API errors are reported
When GitHub rejects the request (invalid token, rate limit, server error), the widget SHALL return an `error` result stating the cause, subject to the stale-data rule of the widget framework.

#### Scenario: Rate limited
- **WHEN** GitHub responds that the rate limit is exceeded
- **THEN** the widget result has status `error` and the message mentions the rate limit
