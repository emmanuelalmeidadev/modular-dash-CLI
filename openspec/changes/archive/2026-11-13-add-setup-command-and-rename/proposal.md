# Proposal

## Why

v1 and v2 work, but the tool is still awkward to adopt as a daily command. Its name, `dash`, is also the system shell on macOS and many Linux systems (`/bin/dash`), so it can be silently shadowed depending on PATH, notably in cron, launchd and other machines. First-run setup is manual (copy a config, create a habits file, pass `--config` every time). The GitHub token has to be exported by hand each session, and one weather timeout was observed on a flaky connection. v3 removes these frictions so the tool can be installed once and used every day.

## What Changes

- **BREAKING**: rename the command from `dash` to `pdash` ("personal dash"). The old entry point is removed. The per-user config and cache directories move to the new name; the cache is disposable and no config file has been required so far.
- Add `pdash init`: creates a starter config at the default config path and a starter habits file, never overwrites existing files, and reports what it created or skipped and what to do next.
- GitHub widget: add an optional `token_cmd` option, a command whose output is the token (for example `gh auth token`), used when the token environment variable is unset. The token is still never stored or printed.
- Weather widget: retry once on a transient network failure before reporting an error.
- Verify a real global install works end to end and document the install steps and the PATH check.
- Assumption (easy to change before apply): the new name is `pdash`. It was chosen because it is unused on this machine and short to type.

## Capabilities

### New Capabilities
- `first-run-setup`: the `init` command that creates a starter config and habits file safely.

### Modified Capabilities
- `dashboard-output`: the command is named `pdash` in the single-pass command, JSON output and dated header requirements.
- `habit-completion`: the command is named `pdash` in the mark-done and invalid-request requirements.
- `github-tasks-widget`: the token may come from a configured command as an alternative to the environment variable.
- `weather-widget`: a transient network failure is retried once before the widget reports an error.

## Impact

- Console script, argparse program name, config and cache directory names, error message prefixes, README and docs, and all tests that invoke the command.
- No new runtime dependencies. `token_cmd` runs a user-configured command; the config file is therefore trusted input (documented).
- Existing v2 specs are modified only where they name the command or the token source.

## Out of Scope

- Renaming the Python package or its import name.
- `habit undo`, a `--watch` refresh mode, new widgets, external-executable plugins.
- Automatic fixing of the user's PATH or shell profile.
