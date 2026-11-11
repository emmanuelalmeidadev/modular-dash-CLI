# Design

## Context

Greenfield: the repository has no code and no existing specs. See proposal.md for motivation. Constraints from exploration: low complexity first, flexibility preserved through one boundary (widgets return data, renderers consume it). Language/runtime was not explicitly chosen by the user; Python was the recommended default and is assumed here.

```
 config --> registry --> [widget.fetch()] x N (parallel, isolated, cached)
                              |
                              v
                        list[WidgetResult]  (plain, JSON-serializable)
                              |
                  +-----------+-----------+
                  v                       v
            terminal renderer        json renderer
```

## Goals / Non-Goals

**Goals:**
- Adding a widget = one new module plus one registry entry; no renderer or config-parser changes for the common case.
- The widget result model is the single contract; JSON output is that model serialized.
- Fast repeated runs, and a dashboard that degrades gracefully.

**Non-Goals:**
- Live/interactive TUI, habit writing, external-executable or drop-in plugins.
- A separate "source" layer. Each widget owns its fetching; a shared source layer is introduced only when a second widget needs the same source.

## Decisions

**D1. Python package with a `dash` console entry point.** Lowest friction for glue code and HTTP. *Alternatives:* TypeScript (comparable), Go/Rust (single binary, more complexity for little gain here). Revisit if distribution as a binary becomes a requirement.

**D2. Widgets are in-process objects behind a small interface:** `id`, `default_ttl`, and `fetch(options) -> data`. A registry maps ids to widgets. The framework, not the widget, wraps fetch into a `WidgetResult` (status, data, error, stale), so widgets just return data or raise. *Alternatives:* drop-in plugin directory (loading, versioning, isolation cost) and external executables (process/protocol cost). The result model is deliberately the shape an external-executable widget would emit, so that path stays open.

**D3. `WidgetResult` is a plain dataclass serialized with the standard `json` module.** No presentation fields. Renderers decide layout. This is what makes `--json` free and renderer swaps cheap.

**D4. Concurrency via a thread pool.** Fetches are I/O-bound HTTP and file reads; threads need no async plumbing in widgets and keep them as plain synchronous functions. A per-widget timeout turns hangs into `error` results. *Alternative:* asyncio (viral `async` in every widget for no gain at this scale).

**D5. Disk cache keyed by widget id plus a hash of its options, stored as JSON files in the platform cache directory.** Each entry stores fetched-at time and data. Only `ok` results are written. On fetch failure an expired entry is served marked stale. Cache never stores secrets: GitHub tokens are read from the environment at fetch time and are not part of options or data.

**D6. Config and habits files are TOML.** Parsed with the standard library, so no parser dependency; human-editable. Config path follows the platform config directory; habits path is a widget option. *Alternative:* YAML (extra dependency, no benefit).

**D7. Terminal rendering with a rendering library; one small render function per widget type, plus a generic fallback that prints a key/value table for unknown shapes.** The JSON renderer is separate and trivial. Color is disabled when stdout is not a TTY or `NO_COLOR` is set.

**D8. Habit streak is computed from a list of completion dates** in the habits file, using the local date, evaluated at run time.

**D9. Weather via a keyless public API; GitHub via its REST search API** using a personal access token from an environment variable. Exact providers are an implementation detail but must satisfy the specs and need no signup for weather.

## Risks / Trade-offs

- [Threads + shared cache files could race] → write cache entries atomically (temp file + rename); one file per entry.
- [Public weather API changes or disappears] → provider isolated inside the weather widget; failure is already an isolated `error`.
- [Generic renderer fallback looks plain] → acceptable for v1; per-widget renderers cover the three built-ins.
- [No plugin system limits third-party extension] → intentional for v1; result model keeps the door open.
- [Python assumed without explicit user confirmation] → flagged in proposal; cheap to change before apply.
