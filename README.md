# dash

A small, modular CLI dashboard. It fetches a few widgets in parallel (weather,
GitHub tasks, habits), prints them once, and exits. Use `--json` to script it.

## Install

Requires Python 3.11+.

```bash
uv venv --python 3.12 && uv pip install -e ".[dev]"   # or: pipx install .
```

## Configure

```bash
cp config.example.toml my-config.toml   # then edit it
dash --config my-config.toml
```

Without `--config`, `dash` looks in your platform config directory and tells
you the exact path if the file is missing. Widgets run in the order listed;
unlisted widgets do not run. Per-widget setup:

- [Weather](docs/weather.md)
- [GitHub tasks](docs/github.md) (needs `GITHUB_TOKEN`)
- [Habits](docs/habits.md)

## Use

```bash
dash                 # render the dashboard once
dash --json          # one JSON document on stdout, nothing else
dash --refresh       # ignore cached results
```

Results from remote widgets are cached (weather 30 min, GitHub 5 min) so
repeat runs are instant. If a fetch fails and an older result exists, it is
shown marked `(stale)`. One failing widget never breaks the others. The exit
status is 0 whenever a dashboard was produced, and non-zero only if `dash`
could not run at all (for example, an invalid config file). Set `NO_COLOR` to
disable styling; output is also plain when piped.

## How it fits together

```
config -> registry -> widgets (parallel, cached, isolated) -> results -> terminal | json
```

A widget returns plain data and knows nothing about rendering. To add one,
implement `id`, `title`, `default_ttl` and `fetch(options) -> dict` (see
`src/dash/widgets/`) and register it in `default_registry()` in `cli.py`.

## Develop

```bash
.venv/bin/pytest
```
# modular-dash-CLI
