# Proposal

## Why

There is no single, scriptable place to glance at daily productivity signals (weather, GitHub work, habits). We want a small CLI dashboard that is cheap to extend: adding a new signal should mean adding one widget, not touching rendering or configuration plumbing. Exploration settled the shape: widgets produce plain data, renderers consume it, and JSON output falls out for free.

## What Changes

- Add a new CLI, `dash`, that renders a dashboard of enabled widgets in one pass and exits (like `git status`).
- Introduce an in-process widget framework: widgets are registered by id, return a JSON-serializable model, are fetched in parallel, and fail in isolation (one broken widget never breaks the dashboard).
- Add a TTL disk cache so repeated runs are fast and external APIs are not hit on every invocation.
- Add three built-in widgets: weather, GitHub tasks (assigned issues / review requests), and habits (read from a local file).
- Add two output modes: a human-readable terminal rendering (tables/panels) and `--json` for scripting.
- Add a single user config file that selects which widgets are enabled, their order, and per-widget options.
- Assumption (recorded, easy to change): implemented in Python, distributed as an installable package. Widgets are in-process only; external-executable and drop-in plugins are out of scope.

## Capabilities

### New Capabilities
- `widget-framework`: widget registration, the widget result model, parallel fetching, per-widget failure isolation, TTL caching, and config-driven selection and ordering of widgets.
- `weather-widget`: current conditions and short forecast for a configured location.
- `github-tasks-widget`: open issues assigned to, and pull requests requesting review from, the authenticated GitHub user.
- `habits-widget`: today's status and current streak for habits defined in a local file (read-only).
- `dashboard-output`: the `dash` command, terminal rendering, and `--json` output.

### Modified Capabilities

(none - the project has no existing specs)

## Impact

- New Python package and `dash` entry point in this repository (currently empty).
- Runtime dependencies: an HTTP client and a terminal-rendering library; config and habit files use TOML so no extra parser dependency is needed.
- External systems: a public weather API (no key) and the GitHub REST API (token via environment variable).
- Writes only to a per-user cache directory; never writes the habits file.

## Out of Scope

- Interactive/live TUI (keys, refresh loop); the renderer boundary keeps it addable later.
- Recording habits (`dash habit done`); v1 is read-only.
- Third-party plugin loading and external-executable widgets.
