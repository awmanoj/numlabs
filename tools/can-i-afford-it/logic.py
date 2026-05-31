"""'Can I afford it?' calculator — pure-Python logic.

Reframe a purchase as *time of your life spent working* for it. Given what you
earn (per hour, week, month or year), your working schedule, and a price tag,
this works out how many hours, days and weeks of work the purchase costs — and
what slice of a month's pay it eats.

The idea (sometimes called "trading life energy for money") is that the honest
price of a thing isn't the number on the tag, it's the hours of your working
life you hand over for it. A $1,200 phone is "three days of work" to one person
and "half a day" to another.

The math is deliberately simple:

  * **Annualise the income** from whatever basis it's quoted in, using the work
    schedule (hours per week × weeks per year) to bridge hourly/weekly figures
    to yearly ones.
  * **Hourly pay** = annual income ÷ (hours per week × weeks per year).
  * Apply an optional **take-home rate** (the share of pay you keep after tax),
    because what you can actually spend is net, not gross.
  * **Hours of work** = price ÷ net hourly pay. Working days assume a 5-day
    week (so a day is ``hours_per_week / 5``); working weeks use the full
    weekly hours; the calendar share is price ÷ net monthly pay.

It's a back-of-the-envelope perspective tool, not budgeting or financial advice.
"""

# Pay bases the income figure can be quoted in.
_BASES = ("hour", "week", "month", "year")

# Sane bounds so a stray 0 or a pasted-in huge number can't produce nonsense.
_MIN_HOURS_PER_WEEK = 1.0
_MAX_HOURS_PER_WEEK = 168.0  # hours in a week
_MIN_WEEKS_PER_YEAR = 1.0
_MAX_WEEKS_PER_YEAR = 53.0

_DAYS_PER_WEEK = 5  # a "work day" is a fifth of the weekly hours


def _num(x, default=0.0):
    """Coerce to float, falling back to ``default`` on junk input."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return default
    if v != v:  # NaN
        return default
    return v


def _annual_income(income, basis, hours_per_week, weeks_per_year):
    """Convert an income quoted on ``basis`` into an annual gross figure."""
    if basis == "hour":
        return income * hours_per_week * weeks_per_year
    if basis == "week":
        return income * weeks_per_year
    if basis == "month":
        return income * 12.0
    # year (and any unexpected basis) is already annual
    return income


def _fmt_hours(hours):
    """Friendly label for a span of working hours.

    Under an hour reads as minutes; otherwise hours and minutes. Very large
    spans drop the trailing minutes — "412 h" is clearer than "412 h 7 min".
    """
    total_min = int(round(hours * 60))
    if total_min <= 0:
        return "0 min"
    if total_min < 60:
        return f"{total_min} min"
    h, m = divmod(total_min, 60)
    if h >= 100 or m == 0:
        return f"{h:,} h"
    return f"{h:,} h {m} min"


def _verdict(months):
    """A plain-language sense of scale from the months-of-pay ratio.

    Framed as how much working time the purchase represents, not as advice on
    whether to buy it.
    """
    if months < 0.05:
        return "Pocket change"
    if months < 0.25:
        return "A small buy"
    if months < 0.75:
        return "Under a month's pay"
    if months < 1.5:
        return "About a month's pay"
    if months < 3:
        return "A couple of months' pay"
    if months < 6:
        return "Several months' pay"
    if months < 12:
        return "Most of a year's pay"
    if months < 24:
        return "Over a year of your pay"
    return "Years of your pay"


def afford(price, income, basis="year", hours_per_week=40,
           weeks_per_year=52, take_home_pct=100):
    """Express ``price`` as time of work for someone earning ``income``.

    ``basis`` is one of ``"hour"``, ``"week"``, ``"month"``, ``"year"`` — the
    period the income is quoted for. ``take_home_pct`` is the share of pay kept
    after tax (100 = use gross). Returns a dict of raw numbers and pre-formatted
    labels; raises ``ValueError`` on inputs that make the math undefined.
    """
    price = _num(price)
    income = _num(income)
    basis = basis if basis in _BASES else "year"

    hours_per_week = max(_MIN_HOURS_PER_WEEK,
                         min(_MAX_HOURS_PER_WEEK, _num(hours_per_week, 40)))
    weeks_per_year = max(_MIN_WEEKS_PER_YEAR,
                         min(_MAX_WEEKS_PER_YEAR, _num(weeks_per_year, 52)))
    take_home_pct = max(1.0, min(100.0, _num(take_home_pct, 100)))

    if price < 0:
        raise ValueError("Price can't be negative.")
    if income <= 0:
        raise ValueError("Enter how much you earn.")

    annual_gross = _annual_income(income, basis, hours_per_week, weeks_per_year)
    if annual_gross <= 0:
        raise ValueError("Enter how much you earn.")

    paid_hours_per_year = hours_per_week * weeks_per_year
    factor = take_home_pct / 100.0

    hourly_gross = annual_gross / paid_hours_per_year
    hourly_net = hourly_gross * factor
    monthly_net = annual_gross * factor / 12.0
    annual_net = annual_gross * factor

    work_hours = price / hourly_net
    hours_per_day = hours_per_week / _DAYS_PER_WEEK
    work_days = work_hours / hours_per_day
    work_weeks = work_hours / hours_per_week
    months_of_pay = price / monthly_net
    pct_of_month = months_of_pay * 100.0

    return {
        "price": price,
        "hourly_gross": hourly_gross,
        "hourly_net": hourly_net,
        "monthly_net": monthly_net,
        "annual_gross": annual_gross,
        "annual_net": annual_net,
        "take_home_pct": take_home_pct,
        "hours_per_day": hours_per_day,
        "work_hours": work_hours,
        "work_days": work_days,
        "work_weeks": work_weeks,
        "months_of_pay": months_of_pay,
        "pct_of_month": pct_of_month,
        "work_hours_label": _fmt_hours(work_hours),
        "verdict": _verdict(months_of_pay),
    }


if __name__ == "__main__":
    # $30/hr, 40h week, 52 weeks. A $1,200 buy is exactly 40 hours of work.
    r = afford(1200, 30, "hour", hours_per_week=40, weeks_per_year=52)
    assert abs(r["work_hours"] - 40) < 1e-9, r["work_hours"]
    assert abs(r["work_days"] - 5) < 1e-9, r["work_days"]       # 40h / 8h day
    assert abs(r["work_weeks"] - 1) < 1e-9, r["work_weeks"]
    assert r["work_hours_label"] == "40 h", r["work_hours_label"]

    # Annual basis: $52,000/yr at 40h × 52wk = $25/hr gross.
    r = afford(250, 52000, "year")
    assert abs(r["hourly_gross"] - 25) < 1e-9, r["hourly_gross"]
    assert abs(r["work_hours"] - 10) < 1e-9, r["work_hours"]

    # Monthly basis annualises by ×12.
    r = afford(0, 5000, "month")
    assert abs(r["annual_gross"] - 60000) < 1e-9, r["annual_gross"]
    assert r["work_hours"] == 0 and r["work_hours_label"] == "0 min"

    # Weekly basis annualises by × weeks_per_year.
    r = afford(100, 1000, "week", weeks_per_year=50)
    assert abs(r["annual_gross"] - 50000) < 1e-9, r["annual_gross"]

    # Take-home rate makes things cost more hours: half the net → double the work.
    full = afford(1000, 50000, "year")
    half = afford(1000, 50000, "year", take_home_pct=50)
    assert abs(half["work_hours"] - 2 * full["work_hours"]) < 1e-6
    assert abs(half["hourly_net"] - full["hourly_net"] / 2) < 1e-9

    # months_of_pay drives the verdict; a small buy vs. a year-plus purchase.
    cheap = afford(50, 60000, "year")            # ~1% of a month
    assert cheap["verdict"] in ("Pocket change", "A small buy"), cheap["verdict"]
    big = afford(80000, 60000, "year")           # 16 months of pay
    assert big["verdict"] == "Over a year of your pay", big["verdict"]

    # Hour/min formatting.
    assert _fmt_hours(0.5) == "30 min"
    assert _fmt_hours(1) == "1 h"
    assert _fmt_hours(1.5) == "1 h 30 min"
    assert _fmt_hours(150) == "150 h"

    # Bad inputs.
    try:
        afford(100, 0, "year")
        assert False, "expected ValueError for zero income"
    except ValueError:
        pass
    try:
        afford(-5, 50000, "year")
        assert False, "expected ValueError for negative price"
    except ValueError:
        pass

    # Clamping: absurd schedule values are pulled into range, not crashed on.
    r = afford(100, 50000, "year", hours_per_week=0, weeks_per_year=999)
    assert r["work_hours"] > 0

    print("all checks passed")
