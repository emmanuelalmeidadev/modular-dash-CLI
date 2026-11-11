# Tasks

## 1. Project scaffold

- [x] 1.1 Create the Python package, `pyproject.toml` with a `dash` console entry point and a test setup; verify `dash --help` runs and the empty test suite passes
- [x] 1.2 Add runtime dependencies (HTTP client, terminal rendering library) and dev dependency (test runner); verify a clean install in a fresh virtual environment succeeds

## 2. Widget framework core

- [x] 2.1 Implement the `WidgetResult` model and its JSON serialization; verify unit tests cover ok, error and stale results round-tripping through JSON
- [x] 2.2 Implement the widget interface and registry with id lookup; verify tests for registering, looking up and an unknown id
- [x] 2.3 Implement config loading (TOML): enabled widgets, order, per-widget options, missing-file and invalid-file messages; verify tests for each scenario in the widget-framework spec
- [x] 2.4 Implement concurrent fetching with per-widget timeout and failure isolation; verify tests that a raising widget and a hanging widget yield `error` results while others stay `ok`, and that two 2s widgets finish in under 4s
- [x] 2.5 Implement the TTL disk cache (atomic writes, options-hash keys, ok-only, stale fallback, `--refresh` bypass); verify tests for hit, expiry, bypass, stale-on-failure and that errors are not cached

## 3. Habits widget

- [x] 3.1 Implement habits file parsing and streak calculation with an injectable "today"; verify tests for continuing streak, not-yet-done today, gap, missing file and malformed file
- [x] 3.2 Verify the habits file is never modified (test comparing file bytes before and after a run) and document the file format in `docs/habits.md` with an example that parses in a test

## 4. Weather widget

- [x] 4.1 Implement the weather widget (location and units options, missing-location error, service-failure error) against a mocked HTTP layer; verify tests for each weather-widget spec scenario
- [x] 4.2 Document weather options in `docs/weather.md`; verify one manual run against the real service returns `ok` for a real location

## 5. GitHub tasks widget

- [x] 5.1 Implement assigned-issues and review-request queries with item limit and totals, token from environment variable only; verify mocked-HTTP tests for listing, empty, truncation, missing token and rate limit
- [x] 5.2 Verify the token never appears in cache files or output (test scanning both) and document setup in `docs/github.md`

## 6. Output and CLI

- [x] 6.1 Implement the JSON renderer and `--json` flag; verify tests that output parses as one document with one entry per widget, including error entries
- [x] 6.2 Implement terminal renderers for the three widgets plus a generic fallback, with error and stale markers and no escape codes when not a TTY or `NO_COLOR` is set; verify snapshot or string tests for each case
- [x] 6.3 Wire `dash` end to end: config, registry, parallel fetch, cache, renderer selection, `--refresh`, exit codes; verify tests for default run, partial failure (exit 0) and invalid config (non-zero)

## 7. Integration

- [x] 7.1 Write a README with install, a sample config file, and sample output; verify following it on a clean environment produces a working dashboard
- [x] 7.2 Run the full test suite and a manual end-to-end run with all three widgets enabled in both terminal and `--json` modes; verify every spec scenario has a passing test or a recorded manual check
