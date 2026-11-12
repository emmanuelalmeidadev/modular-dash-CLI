# Design

## Context

v1 is built and archived (see the main specs). Observed in the current code: `runner.py` serves a cached result as stale when a fetch fails but discards the exception message, although the cache already knows the data's age; `result.py` has a fixed field set serialized by `to_dict`; `cli.py` is a single flat command with `--json`, `--refresh` and `--config`; the habits widget parses its file with the standard-library TOML reader, which cannot write. See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**
- Mark habits done from the CLI without losing anything the user put in the file.
- Make stale data self-explaining and make the dashboard show when it was generated.
- Keep plain `dash` behaving exactly as before, and keep the widget read-only.

**Non-Goals:**
- Undo, listing, or editing habit names from the CLI.
- Fuzzy or prefix name matching.
- Any change to caching rules, TTLs, or how widgets fetch.

## Decisions

**D1. Edit the habits file with a format-preserving TOML library.** Parse the file with the editor library, append the date to the matching habit's `done` array, and serialize. Comments, ordering and unrelated keys survive. *Alternatives:* a plain TOML writer (rewrites everything, loses comments), or a hand-rolled serializer (no dependency, but drops anything outside the documented fields). The extra small, pure-Python dependency is worth keeping the user's file intact.

**D2. Subcommands via argparse subparsers; no subcommand means "show the dashboard".** Existing flags (`--json`, `--refresh`, `--config`) keep working on the default path, and `--config` is also accepted by `habit done`. *Alternative:* a separate `dash-habit` executable (second entry point, duplicated config handling).

**D3. Habits file path comes from the config's habits widget `path` option.** One place defines where the file is, so the widget and the command can never disagree. *Alternative:* a `--file` flag (extra surface; can be added later without breaking this).

**D4. Writing lives in its own module; the widget stays read-only.** Shared pieces (date parsing, name lookup) are reused by both, but only the new module can write. This keeps the v1 guarantee that running the dashboard never modifies the file.

**D5. Safe write sequence:** validate everything first (name, date, not future) so invalid requests touch nothing; copy the current file to `<file>.bak`; write the new contents to a temporary file in the same directory and atomically replace the original. If the backup or the write fails, abort with the original untouched. The backup holds only the most recent previous version.

**D6. Idempotence and ordering:** if the date is already present nothing is written (no backup, no rewrite). New dates are appended; the file's existing order is not reshuffled.

**D7. Stale metadata lives on the result model.** Add optional `stale_reason` and `stale_age_seconds`, populated only on the stale path from the caught exception message and the cache entry's age. `from_dict` tolerates their absence so older data still loads. Renderers read these fields; they never compute them.

**D8. Header and timestamps use one injectable clock** read once per run, so the terminal header and JSON `generated_at` agree and tests need no real time. The header shows weekday, date and time in local time; JSON uses ISO 8601 with the UTC offset.

**D9. Human age formatting is a small pure helper** (seconds, minutes, hours, days) used only by the terminal renderer; JSON keeps raw seconds.

## Risks / Trade-offs

- [New dependency] -> small, pure Python, one import site; if it becomes a problem the writer module is the only thing to swap.
- [User edits the file in an editor while the command runs] -> last write wins; the `.bak` copy limits the damage.
- [Exact name matching can annoy] -> error lists available names; prefix matching can be a later change.
- [Only one backup is kept] -> acceptable for a hand-edited personal file; revisit if it proves insufficient.
- [Library edits an unexpected file shape, for example a habit without a `done` list] -> create the `done` list for that habit, and refuse with a clear message if the file does not match the documented format.
- [Local date near midnight or in another time zone] -> "today" is the machine's local date, same as the widget.

## Open Questions

- Whether to keep more than one backup generation. Safe to defer; it would not change specs or tasks.
