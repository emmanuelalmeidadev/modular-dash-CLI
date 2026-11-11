# GitHub tasks widget

Shows open issues assigned to you and open pull requests waiting for your
review, with repository, number, title, and URL for each.

## Setup

1. Create a GitHub personal access token that can read the repositories you
   care about (a fine-grained token with read access to issues and pull
   requests is enough).
2. Export it in your shell. The token is read **only** from the environment;
   it is never stored in the config file, the cache, or the output.

```bash
export GITHUB_TOKEN=...your token...
```

3. Enable the widget:

```toml
[[widgets]]
id = "github"
ttl = 300   # optional; seconds to cache results (default 300)

[widgets.options]
limit = 5                 # optional; items shown per list (default 5)
token_env = "GITHUB_TOKEN" # optional; name of the environment variable
```

Each list also reports the total count, so you can see when more items exist
than are shown.

## Errors

- Token variable unset: the error names the variable to set.
- Invalid token, rate limit, or GitHub being unreachable: the widget shows an
  error (or the last cached result marked stale).
