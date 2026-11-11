# Habits widget

Shows today's status and current streak for habits you track by hand in a
TOML file. `dash` only ever **reads** this file; it never modifies it.

## Enable it

In your `dash` config:

```toml
[[widgets]]
id = "habits"

[widgets.options]
path = "~/habits.toml"
```

## File format

```toml
[[habits]]
name = "Read 20 pages"
done = ["2026-11-09", "2026-11-10", "2026-11-11"]

[[habits]]
name = "Run"
done = [2026-11-10]
```

- `name` (string, required): shown in the dashboard.
- `done` (list of dates): days you completed it. Dates may be quoted
  `"YYYY-MM-DD"` strings or native TOML dates.

## Streak rules

The streak is the number of consecutive completed days ending **today**, or
ending **yesterday** if today is not done yet (so your streak is not lost
until the day is over). Missing any earlier day resets it to zero.
