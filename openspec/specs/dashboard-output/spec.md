# dashboard-output Specification

## Purpose

Defines the `dash` command and how dashboard results are presented, in a human-readable terminal form and in a machine-readable JSON form.

## Requirements

### Requirement: Single-pass dashboard command
Running `dash` with no subcommand SHALL fetch all configured widgets, print the dashboard once, and exit. It SHALL NOT start an interactive session.

#### Scenario: Default run
- **WHEN** the user runs `dash`
- **THEN** each enabled widget is shown in configured order and the process exits

### Requirement: Terminal rendering
By default the system SHALL render each widget as a titled section with tables or lists suited to its data. An `error` result SHALL render as a visibly marked section with its message. Stale data SHALL be visibly marked as stale.

#### Scenario: Error widget shown inline
- **WHEN** one widget has status `error`
- **THEN** its section shows the error message and the other sections render normally

#### Scenario: Non-terminal output
- **WHEN** standard output is not a terminal, or `NO_COLOR` is set
- **THEN** the output contains no color or cursor escape codes

### Requirement: JSON output
With `--json` the system SHALL print one JSON document to standard output containing every widget result (id, title, status, data, error message if any, stale flag), in configured order, and nothing else on standard output.

#### Scenario: JSON is parseable
- **WHEN** the user runs `dash --json`
- **THEN** standard output parses as a single JSON document with one entry per enabled widget

#### Scenario: JSON includes errors
- **WHEN** a widget fails during `dash --json`
- **THEN** its entry has status `error` and a message, and the command still prints the full document

### Requirement: Exit status
The command SHALL exit with status 0 when the dashboard was produced, even if individual widgets failed, and with a non-zero status when it could not run at all (for example, invalid config).

#### Scenario: Partial failure
- **WHEN** one widget fails but others succeed
- **THEN** the exit status is 0

#### Scenario: Invalid config
- **WHEN** the config file is not valid
- **THEN** the exit status is non-zero and the message identifies the problem
