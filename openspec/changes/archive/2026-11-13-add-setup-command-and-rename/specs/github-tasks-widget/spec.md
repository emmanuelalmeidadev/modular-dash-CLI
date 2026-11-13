# Spec Delta

## RENAMED Requirements

- FROM: `### Requirement: Token from the environment`
- TO: `### Requirement: Token from the environment or a command`

## MODIFIED Requirements

### Requirement: Token from the environment or a command
The widget SHALL authenticate with a token read from an environment variable and, only when that variable is unset, from the output of the command given in the `token_cmd` option. It SHALL NOT read the token from the config file or write it to the cache, output, or logs.

#### Scenario: Token missing
- **WHEN** the token environment variable is unset and no `token_cmd` is configured
- **THEN** the widget returns an `error` result explaining which variable to set and that `token_cmd` is an alternative

#### Scenario: Token from a command
- **WHEN** the environment variable is unset and `token_cmd` is `gh auth token` and that command prints a token
- **THEN** the widget authenticates with that token

#### Scenario: Environment variable wins
- **WHEN** both the environment variable and `token_cmd` are present
- **THEN** the environment variable's value is used and the command is not run

#### Scenario: Token never persisted
- **WHEN** the widget runs successfully with a token
- **THEN** neither the cache files nor the output contain the token value

## ADDED Requirements

### Requirement: Token command is run safely
The widget SHALL run `token_cmd` without a shell and with a time limit, and SHALL use only its trimmed standard output as the token, which MUST be a single word. When the command fails, times out, or prints nothing or more than one word, the widget SHALL return an `error` result that does not include the command's output.

#### Scenario: Command fails
- **WHEN** `token_cmd` exits non-zero
- **THEN** the widget result has status `error`, states that the token command failed, and contains none of the command's output

#### Scenario: Command prints nothing
- **WHEN** `token_cmd` exits successfully but prints only whitespace
- **THEN** the widget result has status `error` stating that the token command produced no token

#### Scenario: Command prints more than a token
- **WHEN** `token_cmd` prints several words or lines
- **THEN** the widget result has status `error` stating the output was not a single token, and the output is not shown

#### Scenario: Command hangs
- **WHEN** `token_cmd` does not finish within its time limit
- **THEN** it is stopped and the widget result has status `error` stating that the token command timed out
