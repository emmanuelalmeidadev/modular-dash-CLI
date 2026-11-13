# GitHub tasks widget

Shows open issues assigned to you and open pull requests waiting for your
review, with repository, number, title, and URL for each.

## Setup

1. Create a GitHub personal access token that can read the repositories you
   care about (a fine-grained token with read access to issues and pull
   requests is enough).
2. Export it in your shell. The token is read from the environment (or from
   `token_cmd`, below); it is never stored in the config file, the cache, or
   the output.

```bash
export GITHUB_TOKEN=...your token...
```

Or, instead of exporting it by hand each session, let a command provide it.
If you use the GitHub CLI (`gh auth login`), set `token_cmd` in the widget
options (see below); `pdash` runs it only when `GITHUB_TOKEN` is unset.

3. Enable the widget:

```toml
[[widgets]]
id = "github"
ttl = 300   # optional; seconds to cache results (default 300)

[widgets.options]
limit = 5                 # optional; items shown per list (default 5)
token_env = "GITHUB_TOKEN" # optional; name of the environment variable
token_cmd = "gh auth token" # optional; command that prints the token
```

## token_cmd

- The command is run **without a shell** (so no pipes, `$VARS` or `;`), with a
  5 second limit. Quote arguments like a shell would:
  `token_cmd = "pass show github/token"`.
- Its output must be a single word (the token). Anything else is an error.
- The environment variable always wins: if `GITHUB_TOKEN` is set, the command
  is not run.
- When it fails, times out, or prints nothing, the widget shows a short error
  such as `token command failed (exit status 1)`. The command's own output is
  never shown, logged or cached.
- **Security:** a config file with `token_cmd` can run a command, so keep your
  config file private and never copy one from someone you do not trust. The
  token itself is never written to the config, the cache, or the output.

Each list also reports the total count, so you can see when more items exist
than are shown.

## Errors

- Token variable unset (and no `token_cmd`): the error names the variable to
  set and mentions `token_cmd` as an alternative.
- Invalid token, rate limit, or GitHub being unreachable: the widget shows an
  error (or the last cached result marked stale).
