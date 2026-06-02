"""Days left on Earth — pure-Python logic.

A blunt little perspective tool. Give it a date of birth and a life
expectancy, and it works out how much of a life has already gone by and how
much — on that estimate — is left: in days, weeks, months, and "summers".

The centrepiece is the **life in weeks** view (after Tim Urban's "Your Life in
Weeks"): a whole human life drawn as a grid where every square is a single
week. Fill in the weeks already lived and the empty squares that remain are
suddenly, uncomfortably countable.

The maths is deliberately plain:

  * **Days lived** = today − date of birth, in whole days.
  * A life of ``life_expectancy`` years is taken as
    ``life_expectancy × 365.25`` days (the .25 keeps leap years honest) and
    ``round(life_expectancy × 52)`` weeks — 52 squares to a row, one row a year.
  * **Weeks lived** = days lived ÷ 7, capped at the total so the grid never
    overflows; **weeks left** is the rest.
  * **Expected date** is the birthday plus the full lifespan in days.
  * Live past the estimate and everything pins to "done": no negative time,
    the grid fills completely, and the framing changes to say so.

Nobody knows their number, and a single average hides a wide spread. This is a
nudge to spend the squares well, not a prediction.
"""

from datetime import date, timedelta

# Sane bounds. Below ~20 the grid is meaningless; above ~125 nobody's gone.
_MIN_LIFE_EXPECTANCY = 1.0
_MAX_LIFE_EXPECTANCY = 125.0

_DAYS_PER_YEAR = 365.25
_WEEKS_PER_YEAR = 52.0
_DAYS_PER_WEEK = 7.0
_DAYS_PER_MONTH = _DAYS_PER_YEAR / 12.0  # 30.4375


def _num(x, default=0.0):
    """Coerce to float, falling back to ``default`` on junk input."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return default
    if v != v:  # NaN
        return default
    return v


def _parse_date(value, default=None):
    """Parse an ISO ``YYYY-MM-DD`` string into a ``date``.

    ``date`` objects pass straight through. ``None``/blank returns ``default``.
    Anything unparseable raises ``ValueError`` so the caller can react.
    """
    if value is None or value == "":
        return default
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _verdict(pct, outlived):
    """A one-line sense of where you are in the run.

    Bands are coarse on purpose — it's a gut-check, not a horoscope.
    """
    if outlived:
        return "Past the estimate — every week is a bonus"
    if pct <= 0:
        return "The whole grid is still empty"
    if pct < 25:
        return "Early days — most of the squares are open"
    if pct < 50:
        return "Still in the first half"
    if pct < 75:
        return "Past the midpoint"
    if pct < 90:
        return "Into the later chapters"
    return "Down to the final rows"


def days_left(birth, life_expectancy=80, today=None):
    """How much of a life is spent and how much is left, on a given estimate.

    ``birth`` is an ISO date string (or ``date``); ``life_expectancy`` is in
    years; ``today`` defaults to the system date but can be pinned (the browser
    passes its own local date so the answer matches the user's calendar).

    Returns a dict of raw numbers plus a few framing fields. Raises
    ``ValueError`` if the birth date is missing, unparseable, or in the future.
    """
    birth = _parse_date(birth)
    if birth is None:
        raise ValueError("A date of birth is required.")
    today = _parse_date(today, default=date.today())

    if birth > today:
        raise ValueError("Date of birth can't be in the future.")

    life_expectancy = max(_MIN_LIFE_EXPECTANCY,
                          min(_MAX_LIFE_EXPECTANCY, _num(life_expectancy, 80)))

    days_lived = (today - birth).days
    days_total = int(round(life_expectancy * _DAYS_PER_YEAR))
    end = birth + timedelta(days=days_total)

    weeks_total = int(round(life_expectancy * _WEEKS_PER_YEAR))
    # Cap the lived count so a long-lived person never overflows the grid.
    weeks_lived = min(weeks_total, int(days_lived // _DAYS_PER_WEEK))
    weeks_left = weeks_total - weeks_lived

    days_left_n = max(0, days_total - days_lived)
    months_left = int(round(days_left_n / _DAYS_PER_MONTH))
    summers_left = max(0, int(round(days_left_n / _DAYS_PER_YEAR)))

    outlived = days_lived >= days_total
    pct_lived = 100.0 if outlived else (days_lived / days_total * 100.0
                                        if days_total else 0.0)

    return {
        "birth": birth.isoformat(),
        "today": today.isoformat(),
        "end": end.isoformat(),
        "life_expectancy": life_expectancy,
        "age_years": days_lived / _DAYS_PER_YEAR,
        "age_years_int": int(days_lived // _DAYS_PER_YEAR),
        "days_lived": days_lived,
        "days_total": days_total,
        "days_left": days_left_n,
        "weeks_lived": weeks_lived,
        "weeks_total": weeks_total,
        "weeks_left": weeks_left,
        "months_left": months_left,
        "summers_left": summers_left,
        "pct_lived": pct_lived,
        "outlived": outlived,
        "verdict": _verdict(pct_lived, outlived),
    }


if __name__ == "__main__":
    # Pin "today" so the assertions are stable regardless of when they run.
    today = date(2026, 1, 1)

    # Born exactly 40 years ago to the day → 40 full years lived.
    r = days_left("1986-01-01", 80, today=today)
    assert r["age_years_int"] == 40, r["age_years_int"]
    assert r["days_lived"] == (date(2026, 1, 1) - date(1986, 1, 1)).days
    # 80 years ≈ 4160 weeks; ~40 years ≈ 2087 weeks lived (with leap days).
    assert r["weeks_total"] == int(round(80 * 52)) == 4160, r["weeks_total"]
    assert r["weeks_lived"] + r["weeks_left"] == r["weeks_total"]
    assert 49 < r["pct_lived"] < 51, r["pct_lived"]  # roughly halfway
    assert r["verdict"] == "Past the midpoint", r["verdict"]
    assert r["end"] == (date(1986, 1, 1)
                        + timedelta(days=int(round(80 * 365.25)))).isoformat()

    # A newborn (born today): nothing lived, the whole grid is open.
    nb = days_left("2026-01-01", 80, today=today)
    assert nb["days_lived"] == 0
    assert nb["weeks_lived"] == 0
    assert nb["weeks_left"] == nb["weeks_total"]
    assert nb["pct_lived"] == 0.0
    assert nb["verdict"] == "The whole grid is still empty"

    # Outliving the estimate pins everything to "done".
    old = days_left("1900-01-01", 80, today=today)
    assert old["outlived"] is True
    assert old["days_left"] == 0
    assert old["weeks_left"] == 0
    assert old["weeks_lived"] == old["weeks_total"]
    assert old["pct_lived"] == 100.0
    assert "bonus" in old["verdict"]

    # weeks_lived is capped exactly at the total even one day over.
    edge = days_left("1946-01-01", 80, today=today)  # 80 years to the day
    assert edge["weeks_lived"] == edge["weeks_total"], edge["weeks_lived"]
    assert edge["weeks_left"] == 0

    # Life expectancy is clamped, not crashed on.
    c = days_left("1986-01-01", 9999, today=today)
    assert c["life_expectancy"] == 125.0
    c2 = days_left("1986-01-01", -5, today=today)
    assert c2["life_expectancy"] == 1.0

    # Bad inputs raise.
    for bad in [(None, 80), ("", 80), ("2099-01-01", 80)]:
        try:
            days_left(bad[0], bad[1], today=today)
            assert False, f"expected ValueError for {bad!r}"
        except ValueError:
            pass

    # Summers-left sanity: ~40 years left on an 80-year estimate.
    assert 39 <= r["summers_left"] <= 41, r["summers_left"]

    print("all checks passed")
