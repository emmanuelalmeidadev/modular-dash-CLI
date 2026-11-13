# Tasks

## 1. Rename to pdash

- [x] 1.1 Change the console script, argparse program name, `pdash:` message prefix, header text and the config and cache directory names to `pdash`, and remove the `dash` script; verify tests for the error prefix, the header, the directory names, and that a fresh install provides `pdash` and no `dash` executable
- [x] 1.2 Update the README, docs, `config.example.toml`, docstrings and every test that invokes or documents the command (including the test that runs commands found in `docs/habits.md`) to the new name; verify a repository-wide search finds no remaining reference to the old command and the full suite passes
- [x] 1.3 Note in the README that the old cache folder can be deleted, and verify the documented install and run commands work as written in a fresh virtual environment

## 2. Setup command

- [x] 2.1 Implement the starter config and habits templates and the create-if-absent writer (temporary file linked into place, skipped when the file exists, no partial file on failure); verify unit tests for create, skip existing, one skipped and one created, missing parent directories, and a simulated write failure leaving nothing behind
- [x] 2.2 Add the `init` subcommand with `--config` and `--location` (quoted safely), the created and skipped report, next steps that mention the token environment variable and `token_cmd`, and non-zero exit on failure; verify CLI tests for each init scenario and that plain `pdash` right after init exits 0
- [x] 2.3 Document `pdash init` in the README, and verify by running init into a temporary location and then the dashboard against it

## 3. GitHub token command

- [x] 3.1 Implement `token_cmd` (no shell, time limit, stdout only, single-word check, fixed error messages, used only when the environment variable is unset); verify tests using small fake commands for success, environment variable precedence, non-zero exit, empty output, multi-word output, a hanging command, and that no error message or result contains the command's output
- [x] 3.2 Update `docs/github.md` with `token_cmd` (including a `gh auth token` example and the note that the config file can run a command), and verify the existing test that scans cache files and output for the token also covers the `token_cmd` path

## 4. Weather retry

- [x] 4.1 Implement one retry on connection errors and timeouts inside an overall 8 second budget shared by the geocode and forecast requests; verify tests for success on retry, failure after two attempts, no retry for an unknown location or an error response, and that total time stays under the budget with a fake slow transport
- [x] 4.2 Verify with a test that a failure after retries still produces the stale-data fallback when a cached result exists, and add a line to `docs/weather.md` describing the retry

## 5. Install and integration

- [x] 5.1 Install the tool globally with `uv tool install` and verify `command -v pdash` resolves to the installed script and `pdash --help` runs from a different directory
- [x] 5.2 Run the full test suite, then verify end to end in temporary locations: `pdash init`, `pdash`, `pdash --json`, and `pdash habit done`, with the token supplied once through the environment variable and once through `token_cmd`
