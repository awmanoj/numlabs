"""Cron expression explainer — pure-Python logic.

Parses a standard 5-field cron expression

    ┌───────────── minute        (0–59)
    │ ┌─────────── hour          (0–23)
    │ │ ┌───────── day of month  (1–31)
    │ │ │ ┌─────── month         (1–12 or JAN–DEC)
    │ │ │ │ ┌───── day of week    (0–6 or SUN–SAT; 7 = Sunday too)
    │ │ │ │ │
    * * * * *

…and turns it into three useful things:

  * a plain-English ``describe`` of the schedule,
  * a per-field ``breakdown`` for a table, and
  * the ``next_runs`` — the upcoming fire times.

Supported field syntax: ``*``, ``,`` (lists), ``-`` (ranges), ``/`` (steps,
including ``*/n`` and ``a/n`` "from a, stepping by n"), three-letter month and
weekday names, and ``?`` (treated as ``*``, for Quartz-style compatibility).
Named macros (``@hourly``, ``@daily``, ``@weekly``, ``@monthly``,
``@yearly``/``@annually``, ``@midnight``) expand to their 5-field form.

The day-of-month / day-of-week quirk is honoured: when **both** fields are
restricted (neither is ``*``), a run fires when **either** matches — the Vixie
cron OR rule. When one is ``*`` it is a plain AND.

``next_runs`` works on naive local datetimes: the browser passes its local
"now" and the results are read back as local time.
"""

from datetime import datetime, timedelta

MONTH_NAMES = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}
DOW_NAMES = {
    "SUN": 0, "MON": 1, "TUE": 2, "WED": 3, "THU": 4, "FRI": 5, "SAT": 6,
}
MONTH_FULL = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
DOW_FULL = [
    "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday",
]

MACROS = {
    "@yearly": "0 0 1 1 *",
    "@annually": "0 0 1 1 *",
    "@monthly": "0 0 1 * *",
    "@weekly": "0 0 * * 0",
    "@daily": "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@hourly": "0 * * * *",
}

# (name, lo, hi, names-dict). DOW parses up to 7 so a literal 7 (Sunday) is
# accepted; it is folded back to 0 below.
FIELD_SPECS = [
    ("minute", 0, 59, None),
    ("hour", 0, 23, None),
    ("day", 1, 31, None),
    ("month", 1, 12, MONTH_NAMES),
    ("dow", 0, 7, DOW_NAMES),
]

HORIZON_YEARS = 5  # how far ahead next_runs will look before giving up


def expand_macro(expr):
    """Return the 5-field form of ``expr``, expanding any ``@macro``."""
    s = expr.strip()
    if s.startswith("@"):
        key = s.lower()
        if key == "@reboot":
            raise ValueError("@reboot has no schedule — it runs once at startup")
        if key not in MACROS:
            raise ValueError(f"Unknown macro '{s}'")
        return MACROS[key]
    return s


def _parse_atom(token, lo, hi, names):
    """Resolve a single value — a number or a three-letter name."""
    t = token.strip()
    if not t:
        raise ValueError("empty value")
    if names and t.upper() in names:
        return names[t.upper()]
    try:
        return int(t)
    except ValueError:
        raise ValueError(f"'{t}' is not a valid value")


def parse_field(raw, lo, hi, names):
    """Parse one cron field into a sorted list of matching integers.

    Returns ``(values, is_star)`` where ``is_star`` is True only when the field
    was literally ``*`` or ``?`` — needed for the DOM/DOW OR rule.
    """
    raw = raw.strip()
    if raw == "":
        raise ValueError("empty field")
    is_star = raw in ("*", "?")
    values = set()

    for item in raw.split(","):
        item = item.strip()
        if not item:
            raise ValueError("empty value in list")

        base, sep, step_s = item.partition("/")
        step = 1
        if sep:
            if not step_s.isdigit() or int(step_s) == 0:
                raise ValueError(f"invalid step in '{item}'")
            step = int(step_s)

        base = base.strip()
        if base in ("*", "?"):
            start, end = lo, hi
        elif "-" in base:
            a, _, b = base.partition("-")
            start = _parse_atom(a, lo, hi, names)
            end = _parse_atom(b, lo, hi, names)
        else:
            start = _parse_atom(base, lo, hi, names)
            # "a/n" with no explicit end means "from a to the maximum".
            end = hi if sep else start

        if start > end:
            raise ValueError(f"range start {start} is after end {end} in '{item}'")
        for v in (start, end):
            if v < lo or v > hi:
                raise ValueError(f"value {v} out of range {lo}–{hi} in '{item}'")

        for v in range(start, end + 1, step):
            values.add(v)

    return sorted(values), is_star


def parse(expr):
    """Parse a full cron expression into a structured dict.

    Keys: per-field ``minute``/``hour``/``day``/``month``/``dow`` (sorted lists),
    ``star`` (per-field bool), ``raw`` (per-field source token) and ``text``
    (the normalized 5-field string). Raises ValueError on anything malformed.
    """
    norm = expand_macro(expr)
    parts = norm.split()
    if len(parts) != 5:
        raise ValueError(
            f"Expected 5 fields, got {len(parts)} — "
            "use: minute hour day-of-month month day-of-week"
        )

    fields, stars, raws = {}, {}, {}
    for token, (name, lo, hi, names) in zip(parts, FIELD_SPECS):
        try:
            vals, is_star = parse_field(token, lo, hi, names)
        except ValueError as e:
            raise ValueError(f"{name} field: {e}")
        if name == "dow":
            # Fold 7 (and the full 0–7 set) down to 0–6, Sunday == 0.
            vals = sorted({0 if v == 7 else v for v in vals})
        fields[name], stars[name], raws[name] = vals, is_star, token

    fields["star"] = stars
    fields["raw"] = raws
    fields["text"] = " ".join(parts)
    return fields


# ── description ────────────────────────────────────────────────────────────

def _list_phrase(items):
    """Join with commas and 'and': [a] → a, [a,b] → a and b, etc."""
    items = [str(i) for i in items]
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def _summarize(values, lo, hi, star):
    """Classify a value set as every / single / range / step / list."""
    vals = sorted(values)
    if star or len(vals) == hi - lo + 1:
        return {"kind": "every"}
    if len(vals) == 1:
        return {"kind": "single", "v": vals[0]}
    diffs = {vals[i + 1] - vals[i] for i in range(len(vals) - 1)}
    if len(diffs) == 1:
        step = next(iter(diffs))
        if step == 1:
            return {"kind": "range", "lo": vals[0], "hi": vals[-1]}
        if vals[0] == lo and vals[-1] + step > hi:
            return {"kind": "step", "step": step}
    return {"kind": "list", "values": vals}


def _minute_phrase(s, minutes):
    k = s["kind"]
    if k == "single":
        return f"minute {s['v']}"
    if k == "range":
        return f"every minute from {s['lo']} through {s['hi']}"
    if k == "step":
        return f"every {s['step']} minutes"
    return "minutes " + _list_phrase(minutes)


def _hour_phrase(s, hours):
    k = s["kind"]
    if k == "every":
        return "every hour"
    if k == "single":
        return f"hour {hours[0]}"
    if k == "range":
        return f"hours {s['lo']} through {s['hi']}"
    if k == "step":
        return f"every {s['step']} hours"
    return "hours " + _list_phrase(hours)


def _time_clause(min_s, hour_s, minutes, hours):
    """English for the combined minute + hour fields."""
    mk, hk = min_s["kind"], hour_s["kind"]

    if mk == "single" and hk == "single":
        return f"at {hours[0]:02d}:{minutes[0]:02d}"
    if mk == "every" and hk == "every":
        return "every minute"
    if mk == "step" and hk == "every":
        return f"every {min_s['step']} minutes"
    if mk == "every":
        return "every minute past " + _hour_phrase(hour_s, hours)
    if mk == "step":
        return f"every {min_s['step']} minutes past " + _hour_phrase(hour_s, hours)
    if hk == "every":
        return f"at {_minute_phrase(min_s, minutes)} past every hour"
    if mk == "single":
        # One minute, several specific hours → list the clock times.
        return "at " + _list_phrase([f"{h:02d}:{minutes[0]:02d}" for h in hours])
    return f"at {_minute_phrase(min_s, minutes)} past {_hour_phrase(hour_s, hours)}"


def _dom_phrase(s, days):
    k = s["kind"]
    if k == "single":
        return f"on day {s['v']} of the month"
    if k == "range":
        return f"on days {s['lo']} through {s['hi']} of the month"
    if k == "step":
        return f"on every {s['step']}th day of the month"
    return "on days " + _list_phrase(days) + " of the month"


def _dow_phrase(s, dows):
    k = s["kind"]
    if k == "single":
        return f"on {DOW_FULL[s['v']]}"
    if k == "range":
        return f"on {DOW_FULL[s['lo']]} through {DOW_FULL[s['hi']]}"
    if k == "step":
        return f"on every {s['step']}th day of the week"
    return "on " + _list_phrase([DOW_FULL[d] for d in dows])


def _month_phrase(s, months):
    k = s["kind"]
    if k == "single":
        return f"in {MONTH_FULL[s['v'] - 1]}"
    if k == "range":
        return f"in {MONTH_FULL[s['lo'] - 1]} through {MONTH_FULL[s['hi'] - 1]}"
    if k == "step":
        return f"in every {s['step']}th month"
    return "in " + _list_phrase([MONTH_FULL[m - 1] for m in months])


def describe(fields):
    """Build a one-sentence plain-English description from parsed fields."""
    star = fields["star"]
    min_s = _summarize(fields["minute"], 0, 59, star["minute"])
    hour_s = _summarize(fields["hour"], 0, 23, star["hour"])
    dom_s = _summarize(fields["day"], 1, 31, star["day"])
    month_s = _summarize(fields["month"], 1, 12, star["month"])
    dow_s = _summarize(fields["dow"], 0, 6, star["dow"])

    time = _time_clause(min_s, hour_s, fields["minute"], fields["hour"])

    clauses = [time]
    dom_star, dow_star = star["day"], star["dow"]
    if not dom_star and not dow_star:
        clauses.append(
            _dom_phrase(dom_s, fields["day"]) + " and "
            + _dow_phrase(dow_s, fields["dow"]) + " (whichever applies)"
        )
    elif not dow_star:
        clauses.append(_dow_phrase(dow_s, fields["dow"]))
    elif not dom_star:
        clauses.append(_dom_phrase(dom_s, fields["day"]))
    elif "every" not in time:
        clauses.append("every day")

    if not star["month"]:
        clauses.append(_month_phrase(month_s, fields["month"]))

    sentence = ", ".join(clauses)
    return sentence[0].upper() + sentence[1:]


def _field_text(name, s, values):
    """Short per-field English for the breakdown table."""
    if name == "minute":
        return {"every": "every minute"}.get(s["kind"]) or _minute_phrase(s, values)
    if name == "hour":
        return _hour_phrase(s, values)
    if name == "day":
        return "every day" if s["kind"] == "every" else _dom_phrase(s, values)[3:]
    if name == "month":
        return "every month" if s["kind"] == "every" else _month_phrase(s, values)[3:]
    if name == "dow":
        return "every day of the week" if s["kind"] == "every" else _dow_phrase(s, values)[3:]
    return ""


FIELD_LABELS = {
    "minute": "Minute", "hour": "Hour", "day": "Day of month",
    "month": "Month", "dow": "Day of week",
}


def breakdown(fields):
    """Per-field rows: label, raw token, and plain English."""
    rows = []
    ranges = {"minute": (0, 59), "hour": (0, 23), "day": (1, 31),
              "month": (1, 12), "dow": (0, 6)}
    for name in ("minute", "hour", "day", "month", "dow"):
        lo, hi = ranges[name]
        s = _summarize(fields[name], lo, hi, fields["star"][name])
        rows.append({
            "label": FIELD_LABELS[name],
            "raw": fields["raw"][name],
            "text": _field_text(name, s, fields[name]),
        })
    return rows


# ── next runs ────────────────────────────────────────────────────────────

def _day_matches(dt, fields):
    """Apply the DOM/DOW match rule for a given date."""
    dom_ok = dt.day in fields["day"]
    cron_dow = (dt.weekday() + 1) % 7  # Python Mon=0..Sun=6 → cron Sun=0..Sat=6
    dow_ok = cron_dow in fields["dow"]
    if fields["star"]["day"] or fields["star"]["dow"]:
        return dom_ok and dow_ok       # the '*' side is always true → plain AND
    return dom_ok or dow_ok            # both restricted → OR


def _next_month_start(dt):
    year, month = (dt.year + 1, 1) if dt.month == 12 else (dt.year, dt.month + 1)
    return dt.replace(year=year, month=month, day=1, hour=0, minute=0)


def _next_day_start(dt):
    return (dt.replace(hour=0, minute=0) + timedelta(days=1))


def _next_hour_start(dt):
    return (dt.replace(minute=0) + timedelta(hours=1))


def next_runs(fields, from_dt=None, count=5):
    """Return up to ``count`` datetimes (strictly after ``from_dt``) that fire.

    Skips coarsely (by month, then day, then hour) so even impossible
    expressions like Feb 30 terminate cheaply at the horizon.
    """
    if from_dt is None:
        from_dt = datetime.now()
    dt = from_dt.replace(second=0, microsecond=0) + timedelta(minutes=1)
    horizon = from_dt.replace(second=0, microsecond=0) + timedelta(days=366 * HORIZON_YEARS)

    out = []
    while len(out) < count and dt <= horizon:
        if dt.month not in fields["month"]:
            dt = _next_month_start(dt)
            continue
        if not _day_matches(dt, fields):
            dt = _next_day_start(dt)
            continue
        if dt.hour not in fields["hour"]:
            dt = _next_hour_start(dt)
            continue
        if dt.minute not in fields["minute"]:
            dt += timedelta(minutes=1)
            continue
        out.append(dt)
        dt += timedelta(minutes=1)
    return out


def explain(expr, from_iso=None, count=5):
    """Full result: normalized text, description, breakdown rows, next runs."""
    fields = parse(expr)
    from_dt = datetime.fromisoformat(from_iso) if from_iso else None
    runs = next_runs(fields, from_dt, count)
    macro = expr.strip().lower() if expr.strip().startswith("@") else ""
    return {
        "normalized": fields["text"],
        "macro": macro,
        "description": describe(fields),
        "fields": breakdown(fields),
        "next_runs": [d.isoformat(timespec="minutes") for d in runs],
    }


def explain_json(expr, from_iso=None, count=5):
    """``explain`` as a JSON string — convenient to JSON.parse in the browser."""
    import json
    return json.dumps(explain(expr, from_iso, count))


if __name__ == "__main__":
    # ── parsing ──
    f = parse("*/15 9-17 * * 1-5")
    assert f["minute"] == [0, 15, 30, 45]
    assert f["hour"] == [9, 10, 11, 12, 13, 14, 15, 16, 17]
    assert f["dow"] == [1, 2, 3, 4, 5]

    # names, 7-as-Sunday, and ? as *
    assert parse("0 0 * JAN-MAR SUN")["month"] == [1, 2, 3]
    assert parse("0 0 * * 7")["dow"] == [0]
    assert parse("0 0 ? * *")["star"]["day"] is True

    # "a/n" means "from a, stepping to the max"
    assert parse("5/15 * * * *")["minute"] == [5, 20, 35, 50]

    # macros
    assert parse("@daily")["text"] == "0 0 * * *"
    assert parse("@weekly")["dow"] == [0]

    # ── descriptions ──
    cases = {
        "* * * * *": "Every minute",
        "*/5 * * * *": "Every 5 minutes",
        "0 * * * *": "At minute 0 past every hour",
        "0 0 * * *": "At 00:00, every day",
        "30 9 * * 1-5": "At 09:30, on Monday through Friday",
        "0 0 1 * *": "At 00:00, on day 1 of the month",
        "0 0 1 1 *": "At 00:00, on day 1 of the month, in January",
        "0 0,12 * * *": "At 00:00 and 12:00, every day",
        "*/15 9-17 * * 1-5":
            "Every 15 minutes past hours 9 through 17, on Monday through Friday",
        "0 0 1 * 1":
            "At 00:00, on day 1 of the month and on Monday (whichever applies)",
    }
    for expr, expected in cases.items():
        got = describe(parse(expr))
        assert got == expected, f"{expr}\n  got:      {got}\n  expected: {expected}"
        print(f"{expr:24s} -> {got}")

    # ── next runs ──
    base = datetime(2026, 6, 26, 9, 0)  # a Friday

    # daily at 00:00: next is tomorrow midnight
    r = next_runs(parse("0 0 * * *"), base, 2)
    assert r[0] == datetime(2026, 6, 27, 0, 0), r[0]
    assert r[1] == datetime(2026, 6, 28, 0, 0)

    # every 15 min during business hours on weekdays — 09:00 already passed (>now)
    r = next_runs(parse("*/15 9-17 * * 1-5"), base, 1)
    assert r[0] == datetime(2026, 6, 26, 9, 15), r[0]

    # DOM/DOW OR rule: 1st of the month OR any Monday
    r = next_runs(parse("0 0 1 * 1"), base, 3)
    # next Monday after Fri Jun 26 is Mon Jun 29, then Wed Jul 1, then Mon Jul 6
    assert r[0] == datetime(2026, 6, 29, 0, 0), r[0]
    assert r[1] == datetime(2026, 7, 1, 0, 0), r[1]
    assert r[2] == datetime(2026, 7, 6, 0, 0), r[2]

    # impossible date terminates at the horizon with no runs
    assert next_runs(parse("0 0 30 2 *"), base, 5) == []

    # explain_json round-trips
    import json
    payload = json.loads(explain_json("30 9 * * 1-5", base.isoformat(), 3))
    assert payload["normalized"] == "30 9 * * 1-5"
    assert len(payload["next_runs"]) == 3
    assert len(payload["fields"]) == 5

    # ── errors ──
    for bad in ["* * * *", "60 * * * *", "* 24 * * *", "0 0 * * 8",
                "* * * FOO *", "5-1 * * * *", "*/0 * * * *", "@reboot"]:
        try:
            parse(bad)
            raise AssertionError(f"expected failure for {bad!r}")
        except ValueError as e:
            print(f"{bad!r:22s} -> {e}")

    print("all checks passed")
