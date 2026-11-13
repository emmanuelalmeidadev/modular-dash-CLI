# pdash

A small, modular CLI dashboard. It fetches a few widgets in parallel (weather,
GitHub tasks, habits), prints them once, and exits. Use `--json` to script it.

## Install

Requires Python 3.11+.

```bash
uv venv --python 3.12 && uv pip install -e ".[dev]"   # or: pipx install .
```

### Install as a global command

```bash
uv tool install .          # or: pipx install .
command -v pdash           # should print the installed path, not nothing
```

The command is named `pdash` on purpose: `dash` is the system shell on
macOS and many Linux systems and can shadow or be shadowed depending on PATH.

Upgrading from the old `dash` command: it no longer exists. The old cache
folder (for example `~/Library/Caches/dash` on macOS) is unused and can be
deleted; the cache and config folders are now named `pdash`.

## Set up (first run)

```bash
pdash init --location "Your City"
```

This creates a starter config in your platform config folder and a starter
`~/habits.toml`, then prints the exact paths and next steps. It never
overwrites a file you already have: existing files are reported as skipped.
Then just run `pdash`. Options:

- `--location CITY` sets the weather city (without it a placeholder is used
  and you are told to change it).
- `--config PATH` writes the config somewhere else; run `pdash --config PATH`
  afterwards.

For GitHub, set the `GITHUB_TOKEN` environment variable, or use `token_cmd`
(see [docs/github.md](docs/github.md)). `init` never asks for or prints a token.

## Configure by hand

```bash
cp config.example.toml my-config.toml   # then edit it
pdash --config my-config.toml
```

Without `--config`, `pdash` looks in your platform config directory and tells
you the exact path if the file is missing. Widgets run in the order listed;
unlisted widgets do not run. Per-widget setup:

- [Weather](docs/weather.md)
- [GitHub tasks](docs/github.md) (needs `GITHUB_TOKEN`)
- [Habits](docs/habits.md)

## Use

```bash
pdash                # render the dashboard once
pdash --json         # one JSON document on stdout, nothing else
pdash --refresh      # ignore cached results
pdash habit done "Read"                     # mark a habit done today
pdash habit done "Read" --date 2026-11-10   # backfill a missed day
```

The terminal output starts with a header showing today's weekday, date and the
time it was generated. `--json` output carries the same moment as
`generated_at`, plus `stale_reason` and `stale_age_seconds` on each widget
(empty unless the data is stale).

Results from remote widgets are cached (weather 30 min, GitHub 5 min) so
repeat runs are instant. If a fetch fails and an older result exists, it is
shown marked `(stale, 2 h old)` with the reason the refresh failed, for
example `Refresh failed: set the GITHUB_TOKEN environment variable`. One failing widget never breaks the others. The exit
status is 0 whenever a dashboard was produced, and non-zero only if `pdash`
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
