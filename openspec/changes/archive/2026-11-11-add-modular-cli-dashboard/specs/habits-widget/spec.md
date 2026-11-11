# Spec Delta

## Purpose

Shows the user's daily habits with today's completion status and current streak, read from a local file the user maintains by hand.

## ADDED Requirements

### Requirement: Habits read from a local file
The widget SHALL read habit definitions and completion dates from a local file whose path is configurable. The widget SHALL NOT modify that file.

#### Scenario: Habits listed
- **WHEN** the file defines two habits
- **THEN** the result lists both, each with its name, whether it is done today, and its current streak in days

#### Scenario: File never written
- **WHEN** the widget runs
- **THEN** the habits file is byte-for-byte unchanged

### Requirement: Streak calculation
A habit's current streak SHALL be the number of consecutive days, ending today or yesterday, on which it was completed. Missing today SHALL NOT break the streak until today has ended; missing any earlier day SHALL.

#### Scenario: Streak continues through today
- **WHEN** a habit was completed on each of the last 3 days including today
- **THEN** its streak is 3 and it is marked done today

#### Scenario: Today not yet done
- **WHEN** a habit was completed yesterday and the day before but not today
- **THEN** its streak is 2 and it is marked not done today

#### Scenario: Gap breaks the streak
- **WHEN** a habit was completed today but not the day before
- **THEN** its streak is 1

### Requirement: Missing or invalid habits file
The widget SHALL return an `error` result when the file is missing or cannot be parsed, with a message naming the path and, for parse errors, the problem location when known.

#### Scenario: File missing
- **WHEN** the configured habits file does not exist
- **THEN** the widget result has status `error` and names the expected path

#### Scenario: Malformed file
- **WHEN** the file contains invalid syntax
- **THEN** the widget result has status `error` describing the parse problem
