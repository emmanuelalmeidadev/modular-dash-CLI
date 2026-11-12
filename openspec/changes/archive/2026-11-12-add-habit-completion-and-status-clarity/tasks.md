# Tasks

## 1. Stale metadata

- [x] 1.1 Add optional `stale_reason` and `stale_age_seconds` to the result model and its dict conversion, tolerating their absence on load; verify unit tests cover fresh, stale and legacy-dict round trips
- [x] 1.2 Populate the reason and cached age on the stale path in the runner; verify tests that a failed fetch with a cached entry yields the exception message and the entry's age, and that fresh and valid-cache results carry neither

## 2. Dashboard output

- [x] 2.1 Add `generated_at` and the stale fields to JSON output using one injectable clock; verify tests for ISO timestamp, stale entry fields, empty fields for non-stale entries, and that stdout is still a single document
- [x] 2.2 Add the dated header and the stale panel reason and age (with a human-readable age helper) to the terminal renderer; verify tests for header content, stale panel text for minutes, hours and days, and no escape codes when piped or with `NO_COLOR`
- [x] 2.3 Update the README output description and verify a real `dash` run shows the header and, with a failing fetch and cached data, a stale panel with reason and age

## 3. Habit completion

- [x] 3.1 Add the format-preserving TOML library as a dependency and verify a clean install in a fresh virtual environment succeeds
- [x] 3.2 Implement habit lookup and completion logic (case-insensitive exact name, idempotent add, rejection of unknown names, malformed and future dates); verify tests for every scenario in the habit-completion spec that does not touch the filesystem
- [x] 3.3 Implement the safe file edit (backup beside the file, atomic replace, abort leaves the original intact, comments and other habits preserved); verify tests for backup content, preserved comments and other habits, no write on duplicate date, and a simulated write failure leaving the original unchanged
- [x] 3.4 Add the `habit done` subcommand with `--date` and `--config`, resolving the file from the habits widget `path` and failing cleanly when no habits widget or no file exists; verify CLI tests for success output, each error exit status, and that plain `dash` and `dash --json` behave as before
- [x] 3.5 Update `docs/habits.md` and the README with the command, the backfill option, the backup file, and an example that is run by a test; verify the documented commands work as written against a temporary habits file

## 4. Integration

- [x] 4.1 Run the full test suite and verify all v1 tests still pass alongside the new ones
- [x] 4.2 Verify end to end on a temporary copy of a real habits file: mark a habit done, see its streak change on the next dashboard run, confirm the `.bak` file and preserved comments, and mark it again to confirm it is idempotent
