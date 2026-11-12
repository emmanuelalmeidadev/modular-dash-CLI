# Spec Delta

## Purpose

Lets the user record a habit as completed on a given day from the command line, so the habits file no longer has to be edited by hand.

## ADDED Requirements

### Requirement: Mark a habit done
The command `dash habit done "<name>"` SHALL add today's local date to the named habit's completion dates in the habits file. The `--date YYYY-MM-DD` option SHALL record that date instead. Names SHALL match case-insensitively and exactly.

#### Scenario: Mark done today
- **WHEN** the user runs `dash habit done "drink water"` and a habit named "Drink water" exists
- **THEN** today's date is added to that habit and the command exits with status 0 and confirms what was recorded

#### Scenario: Backfill a missed day
- **WHEN** the user runs `dash habit done Read --date 2026-11-10`
- **THEN** 2026-11-10 is added to the Read habit, and its streak reflects it on the next dashboard run

### Requirement: Completion is idempotent
Recording a date that is already present for a habit SHALL NOT add a duplicate and SHALL NOT be an error.

#### Scenario: Marking twice
- **WHEN** the user runs the same `habit done` command twice for the same day
- **THEN** the habit has that date exactly once and the second run reports it was already done, exiting with status 0

### Requirement: Invalid requests change nothing
The command SHALL exit non-zero, print a clear message, and leave the habits file unmodified when the name matches no habit, the date is not a valid `YYYY-MM-DD` date, or the date is in the future.

#### Scenario: Unknown habit name
- **WHEN** the user runs `dash habit done Meditate` and no such habit exists
- **THEN** the message lists the available habit names, the exit status is non-zero, and the file is unchanged

#### Scenario: Future date
- **WHEN** the user passes a `--date` later than today
- **THEN** the command refuses with a message, exits non-zero, and the file is unchanged

#### Scenario: Malformed date
- **WHEN** the user passes `--date yesterday`
- **THEN** the command refuses with a message showing the expected format and leaves the file unchanged

### Requirement: Habits file is found through the config
The command SHALL locate the habits file from the `path` option of the configured habits widget, honoring `--config`. It SHALL NOT create a habits file that does not exist.

#### Scenario: No habits widget configured
- **WHEN** the config has no habits widget
- **THEN** the command exits non-zero and says a habits widget with a `path` is required

#### Scenario: File does not exist
- **WHEN** the configured habits file is missing
- **THEN** the command exits non-zero naming the expected path and creates nothing

### Requirement: Safe edit of the habits file
Before changing the habits file the command SHALL save the previous contents to a backup file beside it, and SHALL write the new contents so that a failure leaves the original intact. Everything the command did not need to change, including other habits, their dates and comments, SHALL be preserved.

#### Scenario: Backup written
- **WHEN** a completion is recorded
- **THEN** a `.bak` file next to the habits file contains the file's contents from before the change

#### Scenario: Other content untouched
- **WHEN** a completion is recorded for one habit in a file that contains comments and other habits
- **THEN** every comment and every other habit's name and dates are unchanged in the edited file

#### Scenario: Failure during write
- **WHEN** writing the new contents fails
- **THEN** the original habits file is still present and unchanged and the command exits non-zero
