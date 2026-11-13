# Spec Delta

## MODIFIED Requirements

### Requirement: Single-pass dashboard command
Running `pdash` with no subcommand SHALL fetch all configured widgets, print the dashboard once, and exit. It SHALL NOT start an interactive session.

#### Scenario: Default run
- **WHEN** the user runs `pdash`
- **THEN** each enabled widget is shown in configured order and the process exits

### Requirement: JSON output
With `--json` the system SHALL print one JSON document to standard output containing a `generated_at` timestamp and every widget result (id, title, status, data, error message if any, stale flag, stale reason, stale age in seconds), in configured order, and nothing else on standard output.

#### Scenario: JSON is parseable
- **WHEN** the user runs `pdash --json`
- **THEN** standard output parses as a single JSON document with one entry per enabled widget

#### Scenario: JSON includes errors
- **WHEN** a widget fails during `pdash --json`
- **THEN** its entry has status `error` and a message, and the command still prints the full document

#### Scenario: JSON includes generation time
- **WHEN** the user runs `pdash --json`
- **THEN** the document has a `generated_at` timestamp in ISO 8601 form

#### Scenario: JSON stale entry
- **WHEN** a widget is served stale during `pdash --json`
- **THEN** its entry has the stale flag set, a stale reason, and a stale age in seconds, and these are empty for non-stale entries

### Requirement: Dated header
Terminal output SHALL begin with a header showing the current weekday and local date and the local time at which the dashboard was generated.

#### Scenario: Header shown
- **WHEN** the user runs `pdash` on Thursday 2026-11-12 at 14:03
- **THEN** the first line of output shows the weekday, the date 2026-11-12, and the time 14:03

#### Scenario: Header without styling
- **WHEN** output is not a terminal or `NO_COLOR` is set
- **THEN** the header is still printed, without color or escape codes

## ADDED Requirements

### Requirement: Command name
The tool SHALL be invoked as `pdash`. The former name `dash` SHALL NOT be installed, so that it cannot shadow or be shadowed by the system shell of the same name. Error messages SHALL be prefixed with the command name.

#### Scenario: Installed command
- **WHEN** the tool is installed
- **THEN** a `pdash` executable is provided and no `dash` executable is provided

#### Scenario: Error prefix
- **WHEN** the command fails with an error message
- **THEN** the message begins with `pdash:`
