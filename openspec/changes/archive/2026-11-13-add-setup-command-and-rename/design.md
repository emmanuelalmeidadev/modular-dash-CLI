# Design

## Context

v1 and v2 are built, archived and committed. Observed in the current code: the console script, the argparse program name, the `dash:` message prefix, the header text and both platform directories (`user_config_path("dash")`, `user_cache_path("dash")`) all use the name `dash`; the GitHub widget reads its token only from an environment variable; the weather widget makes two requests (geocode, forecast) with an 8 s client timeout and no retry; the framework turns a widget timeout (default 10 s) into a plain error and does not consult the cache in that case, whereas a raised exception falls back to stale data. On this machine `~/.local/bin` precedes `/bin` on PATH, so a global install would win over `/bin/dash`, but that is not true everywhere (cron, launchd, other machines). See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**
- One name with no system collision, used consistently by script, messages, docs and data directories.
- A fresh install reaches a working dashboard with one command and no manual file copying.
- No secret ever stored by the tool; an alternative to hand-exporting the token each session.
- Weather survives a one-off network hiccup without losing the stale-data fallback.

**Non-Goals:**
- Renaming the Python package `dash` (it only matters if the Plotly package of the same import name is installed in the same environment; global tool installs are isolated).
- Making widget timeouts fall back to stale data. This is a pre-existing framework gap, noted under Risks.
- Editing the user's shell profile or PATH.

## Decisions

**D1. Rename by changing the console script, program name, message prefix and header; remove the old script.** The package keeps its import name, so no source files move. The config and cache directories are renamed to match (`pdash`). The old cache directory is disposable and no config has been required so far, so there is no migration; the README mentions the old cache folder can be deleted. *Alternatives:* keep both scripts (keeps the collision), or only document PATH ordering (fragile, easy to forget).

**D2. `init` is a subcommand that writes from in-code templates.** The starter config and starter habits text are constants in one module; `--location` is inserted as a properly quoted TOML string. *Alternative:* copy a bundled data file (packaging overhead for two small files).

**D3. Create-if-absent without overwrite or partial files:** write the content to a temporary file in the destination directory, then link it into place, which fails if the destination exists (reported as skipped); remove the temporary file afterwards. *Alternatives:* open with exclusive-create (can leave a partial file if the write fails midway), or check-then-write (race).

**D4. Starter config uses `~/habits.toml` for the habits path and enables all three widgets.** Without `--location` the weather location is a clearly marked placeholder city, and init's output tells the user to edit it. Habits are three example habits with empty completion lists, matching the existing docs.

**D5. `token_cmd` runs through the subprocess API with an argument list (split with shell-style quoting rules), no shell, a 5 s timeout, stdout captured and stderr discarded.** Only the trimmed stdout is used and it must be one word; every failure mode maps to a fixed message that never includes the output. It runs only when the environment variable is unset. The config file is therefore trusted input that can execute a command, which the docs state plainly. *Alternatives:* auto-detecting `gh` without being asked (implicit execution), or a keychain integration (platform-specific, larger).

**D6. Weather retry uses an overall time budget.** A deadline of 8 s covers all attempts across both requests; each attempt's timeout is the smaller of 4 s and the time remaining, and a retry happens only if at least 1 s remains. Only connection errors and timeouts are retried. This keeps the widget under the 10 s framework timeout, so a failed run still raises an exception and the stale fallback still applies. *Alternative:* fixed per-attempt timeouts (can exceed the framework timeout and silently lose the fallback).

**D7. Install verification is a task, not code.** The README documents `uv tool install` (or `pipx`) and a PATH check (`command -v pdash`), and the apply phase verifies a real global install from a different directory.

## Risks / Trade-offs

- [Breaking rename] -> single user today; stated as BREAKING in the proposal; old script removed so nothing silently runs the wrong tool.
- [`token_cmd` executes a command from the config] -> no shell, time limit, fixed error messages, only used when the env var is unset, documented as trusted-config behavior.
- [A hung widget still bypasses stale data] -> pre-existing; the retry budget avoids making it worse; a follow-up change could let timeouts use the cache.
- [Placeholder weather location may be left unedited] -> init output names it; weather shows the placeholder city openly instead of failing.
- [Hard links unsupported on some filesystems] -> init falls back to reporting a clear write error rather than overwriting.
- [Package import name `dash` clashes with the Plotly package if both share an environment] -> out of scope; tool installs are isolated; revisit if it ever bites.

## Open Questions

- Whether `pdash init` should later offer an interactive mode for location and token command. Safe to defer; it would not change specs or tasks.
