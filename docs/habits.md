# Habits widget

Shows today's status and current streak for habits you track by hand in a
TOML file. Showing the dashboard only ever **reads** this file. The only thing
that writes to it is the explicit `pdash habit done` command (see below).

## Enable it

In your `pdash` config:

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

## Mark a habit done

Instead of editing the file, record a completion from the command line:

```bash
pdash habit done "Run"
pdash habit done "Read 20 pages" --date 2026-11-10
```

- The name is matched case-insensitively and must match exactly. An unknown
  name lists the habits you do have.
- With no `--date` it records today (local date). `--date YYYY-MM-DD` backfills
  a missed day; future dates are refused.
- Running the same command twice is safe: the date is stored once.
- The file is found through your config: the `path` option of the `habits`
  widget. Use `--config PATH` if your config is not in the default place.

Your comments and the rest of the file are kept as they are. Before each
change the previous contents are saved next to the file as `habits.toml.bak`
(only the latest previous version is kept). If anything fails, your original
file is left untouched, and the command never creates a missing file.
