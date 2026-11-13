# first-run-setup Specification

## Purpose

Gets a new user from a fresh install to a working dashboard with one command, by creating a starter config and habits file without ever overwriting the user's own files.

## Requirements

### Requirement: Create starter files
The command `pdash init` SHALL create a starter config file at the default config path (or at the path given by `--config`) and a starter habits file at the path the starter config references. Missing parent directories SHALL be created.

#### Scenario: Fresh machine
- **WHEN** the user runs `pdash init` and neither file exists
- **THEN** both files are created and the command exits with status 0

#### Scenario: Custom config path
- **WHEN** the user runs `pdash init --config ./my-config.toml`
- **THEN** the starter config is written to that path instead of the default

### Requirement: Existing files are never overwritten
If a file that init would create already exists, init SHALL leave it unchanged, report it as skipped, and still create any other missing file.

#### Scenario: Config already exists
- **WHEN** the config file exists and the habits file does not
- **THEN** the config is byte-for-byte unchanged, the habits file is created, and the output names the config as skipped

#### Scenario: Everything exists
- **WHEN** both files already exist
- **THEN** nothing is written, both are reported as skipped, and the exit status is 0

### Requirement: Starter files are immediately usable
The starter config SHALL enable the weather, GitHub and habits widgets, and the starter habits file SHALL define a few example habits with no completions. Running `pdash` right after init SHALL NOT fail on configuration errors. A `--location` option SHALL set the weather location.

#### Scenario: Dashboard runs after init
- **WHEN** the user runs `pdash init` and then `pdash`
- **THEN** the dashboard is printed and the exit status is 0

#### Scenario: Location option
- **WHEN** the user runs `pdash init --location Culiacan`
- **THEN** the starter config sets the weather location to Culiacan

### Requirement: Init reports what happened and what is next
Init SHALL print each path it created or skipped, and next steps: where to edit the config, and how to provide a GitHub token. It SHALL NOT print or ask for a token value.

#### Scenario: Next steps shown
- **WHEN** init completes
- **THEN** the output lists created and skipped paths and mentions the token environment variable and the `token_cmd` option

### Requirement: Init failures are clear
If a file cannot be written, init SHALL exit non-zero with a message naming the path and the cause, and SHALL NOT leave a partially written file at that path.

#### Scenario: Unwritable directory
- **WHEN** the config directory cannot be created or written
- **THEN** the command exits non-zero, names the path and the cause, and no partial file remains
