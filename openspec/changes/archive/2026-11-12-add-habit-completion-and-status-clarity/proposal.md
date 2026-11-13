# Proposal

## Why

Using v1 for a day exposed three gaps that keep it from being a daily driver: habits can only be completed by editing a TOML file by hand, a `(stale)` panel gives no hint why the fetch failed, and nothing on screen shows today's date or how old the data is. Each is small, but together they decide whether the dashboard is trusted and used every day.

## What Changes

- Add `dash habit done "<name>"` to record a habit as completed for today, with `--date YYYY-MM-DD` to backfill a missed day. It is idempotent and rejects unknown names and future dates.
- The command edits the habits file in place, keeping one file as the source of truth. Comments, formatting and unrelated content are preserved, and a `.bak` copy of the previous contents is written first as a safety net.
- Stale results now carry the reason the fresh fetch failed and the age of the cached data, and both are shown on the stale panel and in JSON output.
- The terminal dashboard prints a header with today's date and the time it was generated; JSON output gains a matching `generated_at` field.
- The habits widget itself stays read-only: only the explicit `habit done` command writes.

## Capabilities

### New Capabilities
- `habit-completion`: recording a habit as completed on a given day from the command line, including validation, idempotency, and safe rewriting of the habits file.

### Modified Capabilities
- `widget-framework`: stale results must carry the failure reason and the age of the cached data.
- `dashboard-output`: add a dated header, show reason and age on stale panels, and extend the JSON output with `generated_at`, `stale_reason` and `stale_age_seconds`.

## Impact

- `dash` gains a subcommand; running `dash` with no subcommand behaves as before.
- Code touched: result model, runner (stale path), both renderers, CLI argument parsing; new habit-writing module.
- New runtime dependency: a format-preserving TOML editor (the standard library only reads TOML).
- Writes to the user's habits file for the first time, plus a `.bak` file beside it.
- JSON consumers see additive fields only; no existing field changes.

## Out of Scope

- `dash init` / easier first-run setup, token keychain support, `habit undo`, live TUI, plugin or external widgets.
