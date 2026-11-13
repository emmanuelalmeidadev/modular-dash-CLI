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
With `--json` the system SHALL print one JSON document to standard output containing a `generated_at` timestamp and every widget result (id, title, status, data, error message if any, stale flag, stale reason, stale age in seconds), in configured order, and nothing else on standard output.

#### Scenario: JSON is parseable
- **WHEN** the user runs `dash --json`
- **THEN** standard output parses as a single JSON document with one entry per enabled widget

#### Scenario: JSON includes errors
- **WHEN** a widget fails during `dash --json`
- **THEN** its entry has status `error` and a message, and the command still prints the full document

#### Scenario: JSON includes generation time
- **WHEN** the user runs `dash --json`
- **THEN** the document has a `generated_at` timestamp in ISO 8601 form

#### Scenario: JSON stale entry
- **WHEN** a widget is served stale during `dash --json`
- **THEN** its entry has the stale flag set, a stale reason, and a stale age in seconds, and these are empty for non-stale entries

### Requirement: Exit status
The command SHALL exit with status 0 when the dashboard was produced, even if individual widgets failed, and with a non-zero status when it could not run at all (for example, invalid config).

#### Scenario: Partial failure
- **WHEN** one widget fails but others succeed
- **THEN** the exit status is 0

#### Scenario: Invalid config
- **WHEN** the config file is not valid
- **THEN** the exit status is non-zero and the message identifies the problem

### Requirement: Dated header
Terminal output SHALL begin with a header showing the current weekday and local date and the local time at which the dashboard was generated.

#### Scenario: Header shown
- **WHEN** the user runs `dash` on Thursday 2026-11-12 at 14:03
- **THEN** the first line of output shows the weekday, the date 2026-11-12, and the time 14:03

#### Scenario: Header without styling
- **WHEN** output is not a terminal or `NO_COLOR` is set
- **THEN** the header is still printed, without color or escape codes

### Requirement: Stale panels show reason and age
A stale widget panel SHALL show how old the displayed data is, in human-readable units, and the reason the fresh fetch failed.

#### Scenario: Stale panel details
- **WHEN** a widget is served stale because GitHub rejected the request, with data two hours old
- **THEN** the panel is marked stale and shows an age of about 2 hours and the failure message
