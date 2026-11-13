# Spec Delta

## MODIFIED Requirements

### Requirement: Mark a habit done
The command `pdash habit done "<name>"` SHALL add today's local date to the named habit's completion dates in the habits file. The `--date YYYY-MM-DD` option SHALL record that date instead. Names SHALL match case-insensitively and exactly.

#### Scenario: Mark done today
- **WHEN** the user runs `pdash habit done "drink water"` and a habit named "Drink water" exists
- **THEN** today's date is added to that habit and the command exits with status 0 and confirms what was recorded

#### Scenario: Backfill a missed day
- **WHEN** the user runs `pdash habit done Read --date 2026-11-10`
- **THEN** 2026-11-10 is added to the Read habit, and its streak reflects it on the next dashboard run

### Requirement: Invalid requests change nothing
The command SHALL exit non-zero, print a clear message, and leave the habits file unmodified when the name matches no habit, the date is not a valid `YYYY-MM-DD` date, or the date is in the future.

#### Scenario: Unknown habit name
- **WHEN** the user runs `pdash habit done Meditate` and no such habit exists
- **THEN** the message lists the available habit names, the exit status is non-zero, and the file is unchanged

#### Scenario: Future date
- **WHEN** the user passes a `--date` later than today
- **THEN** the command refuses with a message, exits non-zero, and the file is unchanged

#### Scenario: Malformed date
- **WHEN** the user passes `--date yesterday`
- **THEN** the command refuses with a message showing the expected format and leaves the file unchanged
