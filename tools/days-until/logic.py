"""Days until — countdown math, pure Python.

Given "now" and a target moment, break the gap down every way people ask for
it: total days / weeks / hours, a calendar years-months-days split, working
days (Mon–Fri), a live D-H-M-S remainder, and how far through the current year
we already are.

The browser passes both timestamps in as ISO strings so the math stays a pure
function of its inputs — no hidden `date.today()` — which keeps it testable in
CPython and identical in Pyodide. Runs standalone: `python3 logic.py`.
"""

import calendar
from datetime import date, datetime, timedelta

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday", "Sunday"]


def parse_dt(s):
    """Parse 'YYYY-MM-DD' or 'YYYY-MM-DDTHH:MM[:SS]' into a datetime.

    A bare date is treated as midnight at the start of that day.
    """
    s = s.strip().replace(" ", "T")
    if "T" in s:
        d, t = s.split("T", 1)
        parts = [int(p) for p in t.split(":")]
        parts += [0] * (3 - len(parts))
        y, m, day = (int(x) for x in d.split("-"))
        return datetime(y, m, day, parts[0], parts[1], parts[2])
    y, m, day = (int(x) for x in s.split("-"))
    return datetime(y, m, day)


def calendar_breakdown(d1, d2):
    """Years / months / days between two dates, with d1 <= d2.

    Borrows a real calendar month (not a flat 30) when the day rolls under,
    so '2026-01-31 → 2026-03-01' reads the way a human would count it.
    """
    years = d2.year - d1.year
    months = d2.month - d1.month
    days = d2.day - d1.day
    if days < 0:
        months -= 1
        prev_month = d2.month - 1 or 12
        prev_year = d2.year if d2.month > 1 else d2.year - 1
        days += calendar.monthrange(prev_year, prev_month)[1]
    if months < 0:
        years -= 1
        months += 12
    return years, months, days


def business_days_between(d1, d2):
    """Weekdays (Mon–Fri) strictly after d1, up to and including d2.

    Counts the working days you'd cross waiting from d1 for the target d2.
    """
    if d2 <= d1:
        return 0
    # Whole weeks contribute 5 each; sweep only the ragged tail.
    total = 0
    d = d1 + timedelta(days=1)
    while d <= d2:
        if d.weekday() < 5:
            total += 1
        d += timedelta(days=1)
    return total


def year_progress(d):
    """How far through d's calendar year we are: elapsed / left / percent."""
    start = date(d.year, 1, 1)
    days_in_year = 366 if calendar.isleap(d.year) else 365
    day_of_year = (date(d.year, d.month, d.day) - start).days + 1
    days_left = days_in_year - day_of_year
    return {
        "year": d.year,
        "day_of_year": day_of_year,
        "days_in_year": days_in_year,
        "days_left": days_left,
        "percent": round(100 * day_of_year / days_in_year, 1),
    }


def countdown(now_iso, target_iso):
    """Full countdown from `now_iso` to `target_iso` (both ISO strings)."""
    now = parse_dt(now_iso)
    target = parse_dt(target_iso)

    secs = (target - now).total_seconds()
    if abs(secs) < 60:
        direction = "now"
    elif secs > 0:
        direction = "future"
    else:
        direction = "past"

    abs_secs = abs(secs)
    total_days = int(abs_secs // 86400)
    total_hours = int(abs_secs // 3600)
    total_minutes = int(abs_secs // 60)

    # D-H-M-S remainder for a live ticker.
    rem = abs_secs
    d_part = int(rem // 86400); rem -= d_part * 86400
    h_part = int(rem // 3600);  rem -= h_part * 3600
    m_part = int(rem // 60);    s_part = int(rem - m_part * 60)

    lo, hi = sorted([now.date(), target.date()])
    years, months, days = calendar_breakdown(lo, hi)

    return {
        "direction": direction,
        "target_weekday": WEEKDAYS[target.weekday()],
        "total_days": total_days,
        "total_weeks": total_days // 7,
        "weeks_remainder_days": total_days % 7,
        "total_hours": total_hours,
        "total_minutes": total_minutes,
        "business_days": business_days_between(lo, hi),
        "cal_years": years,
        "cal_months": months,
        "cal_days": days,
        "remaining": {"days": d_part, "hours": h_part,
                      "minutes": m_part, "seconds": s_part},
        "year_progress": year_progress(now.date()),
    }


if __name__ == "__main__":
    # A clean, checkable span: exactly one non-leap year, 8 hours apart.
    r = countdown("2026-01-01T00:00", "2027-01-01T08:00")
    assert r["direction"] == "future"
    assert r["total_days"] == 365, r["total_days"]
    assert (r["cal_years"], r["cal_months"], r["cal_days"]) == (1, 0, 0), r
    assert r["target_weekday"] == "Friday", r["target_weekday"]
    assert r["remaining"]["hours"] == 8, r["remaining"]
    # 2026 has 261 weekdays; midnight-to-midnight the count is right.
    assert business_days_between(date(2026, 1, 1), date(2027, 1, 1)) == 261

    # Month borrow across a 28-day February: Jan 15 → Mar 10 = 1 month, 23 days
    # (Jan 15 +1mo = Feb 15, then 13 days to Feb 28 + 10 = 23).
    assert calendar_breakdown(date(2026, 1, 15), date(2026, 3, 10)) == (0, 1, 23)

    # Past dates report as past.
    assert countdown("2026-07-01", "2026-06-01")["direction"] == "past"

    print("Countdown 2026-01-01 → 2027-01-01 08:00")
    print(f"  {r['total_days']} days · {r['total_weeks']} weeks "
          f"+ {r['weeks_remainder_days']} days")
    print(f"  {r['business_days']} working days")
    print(f"  calendar: {r['cal_years']}y {r['cal_months']}m {r['cal_days']}d, "
          f"lands on a {r['target_weekday']}")
    yp = year_progress(date(2026, 7, 1))
    print(f"  {yp['year']} is {yp['percent']}% gone "
          f"({yp['days_left']} days left)")
