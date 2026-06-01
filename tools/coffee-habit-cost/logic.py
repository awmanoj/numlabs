"""Coffee habit cost — pure-Python logic.

Take a small, recurring purchase — the daily coffee is the classic one — and
show what it actually adds up to. A ₹150 cup once a day is ₹150 × 365 ≈
₹54,750 a year. Spell that out over a few years, and then over the same span if
the money had been *invested* instead of sipped, and a quiet habit turns into a
surprisingly large number.

The math is deliberately simple:

  * **Per occasion** is just the price of one cup.
  * **Per day** = price × cups per day.
  * A year has the habit on ``days_per_week / 7`` of its days, so
    **yearly** = per-day × (days_per_week / 7) × 365. At 7 days a week that is
    the familiar "× 365"; weekday-only (5/7) scales it down.
  * **Weekly** = per-day × days per week; **monthly** = yearly ÷ 12.
  * **Projected spend** over N years is just yearly × N — money out the door.
  * **If invested instead**, the monthly cost is treated as a monthly deposit
    into an account returning ``annual_return`` percent, compounded monthly, for
    N years (a standard future-value-of-an-annuity). The gap between that and
    the plain projected spend is the real cost of the habit.

It's a perspective tool, not a lecture: nothing here says don't enjoy the
coffee, only what the habit costs if you ever want to weigh it.
"""

# Sane bounds so a stray 0 or a pasted-in huge number can't produce nonsense.
_MIN_DAYS_PER_WEEK = 0.0
_MAX_DAYS_PER_WEEK = 7.0
_MIN_YEARS = 0.0
_MAX_YEARS = 100.0

_DAYS_PER_YEAR = 365.0
_MONTHS_PER_YEAR = 12.0


def _num(x, default=0.0):
    """Coerce to float, falling back to ``default`` on junk input."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return default
    if v != v:  # NaN
        return default
    return v


def _future_value_annuity(monthly, annual_return_pct, years):
    """Future value of depositing ``monthly`` every month for ``years``.

    Contributions are made monthly and compounded at ``annual_return_pct`` a
    year (split into 12 monthly periods). With a zero return this is just the
    sum of the deposits. Returns the end balance.
    """
    n = int(round(years * _MONTHS_PER_YEAR))
    if n <= 0 or monthly <= 0:
        return 0.0
    i = annual_return_pct / 100.0 / _MONTHS_PER_YEAR
    if i == 0:
        return monthly * n
    return monthly * ((1 + i) ** n - 1) / i


def _verdict(yearly):
    """A plain-language sense of scale for the yearly cost, framed in pay.

    The bands are deliberately coarse — this is a gut-check, not a budget.
    """
    if yearly <= 0:
        return "No habit, no cost"
    if yearly < 1000:
        return "Barely a blip"
    if yearly < 10000:
        return "Adds up quietly"
    if yearly < 50000:
        return "A real line item"
    if yearly < 150000:
        return "A holiday's worth, yearly"
    return "Serious money, yearly"


def coffee(price, cups_per_day=1, days_per_week=7, years=10,
           annual_return=7):
    """Cost of a recurring ``price`` cup, ``cups_per_day`` a day.

    ``days_per_week`` is how many days a week the habit happens (7 = every day,
    5 = weekdays only). ``years`` is the projection horizon and
    ``annual_return`` the percent return used for the "if invested instead"
    figure. Returns a dict of raw numbers and pre-formatted labels; raises
    ``ValueError`` on inputs that make the math undefined.
    """
    price = _num(price)
    cups_per_day = _num(cups_per_day, 1)
    days_per_week = max(_MIN_DAYS_PER_WEEK,
                        min(_MAX_DAYS_PER_WEEK, _num(days_per_week, 7)))
    years = max(_MIN_YEARS, min(_MAX_YEARS, _num(years, 10)))
    annual_return = max(0.0, _num(annual_return, 7))

    if price < 0:
        raise ValueError("Price can't be negative.")
    if cups_per_day < 0:
        raise ValueError("Cups per day can't be negative.")

    per_day = price * cups_per_day
    week_fraction = days_per_week / 7.0

    weekly = per_day * days_per_week
    yearly = per_day * week_fraction * _DAYS_PER_YEAR
    monthly = yearly / _MONTHS_PER_YEAR
    daily_avg = yearly / _DAYS_PER_YEAR  # spread across every day of the year

    projected_spend = yearly * years
    invested = _future_value_annuity(monthly, annual_return, years)
    invested_gain = invested - monthly * round(years * _MONTHS_PER_YEAR)
    # "Cost" of the habit if you'd otherwise have invested the money: the pot it
    # would have grown into. Falls back to plain spend when no return is set.
    opportunity = invested if invested > projected_spend else projected_spend

    return {
        "price": price,
        "cups_per_day": cups_per_day,
        "days_per_week": days_per_week,
        "years": years,
        "annual_return": annual_return,
        "per_day": per_day,
        "daily_avg": daily_avg,
        "weekly": weekly,
        "monthly": monthly,
        "yearly": yearly,
        "projected_spend": projected_spend,
        "invested": invested,
        "invested_gain": invested_gain,
        "opportunity": opportunity,
        "verdict": _verdict(yearly),
    }


if __name__ == "__main__":
    # The headline example: ₹150 a cup, once a day, every day → ₹54,750 a year.
    r = coffee(150, 1, 7, years=10, annual_return=0)
    assert abs(r["yearly"] - 150 * 365) < 1e-9, r["yearly"]
    assert abs(r["yearly"] - 54750) < 1e-9, r["yearly"]
    assert abs(r["per_day"] - 150) < 1e-9, r["per_day"]
    assert abs(r["weekly"] - 150 * 7) < 1e-9, r["weekly"]
    assert abs(r["monthly"] - 54750 / 12) < 1e-9, r["monthly"]

    # Two cups doubles everything.
    r2 = coffee(150, 2, 7, years=10, annual_return=0)
    assert abs(r2["yearly"] - 2 * 54750) < 1e-9, r2["yearly"]

    # Weekday-only (5/7) scales the yearly cost by 5/7.
    wd = coffee(150, 1, 5, years=10, annual_return=0)
    assert abs(wd["yearly"] - 150 * (5 / 7) * 365) < 1e-6, wd["yearly"]
    assert abs(wd["weekly"] - 150 * 5) < 1e-9, wd["weekly"]

    # No return → invested equals plain projected spend (sum of deposits).
    flat = coffee(150, 1, 7, years=10, annual_return=0)
    assert abs(flat["projected_spend"] - 54750 * 10) < 1e-6, flat["projected_spend"]
    assert abs(flat["invested"] - flat["monthly"] * 120) < 1e-6, flat["invested"]
    assert flat["invested_gain"] == 0 or abs(flat["invested_gain"]) < 1e-6
    assert abs(flat["opportunity"] - flat["projected_spend"]) < 1e-6

    # With a positive return the invested pot beats the money spent.
    grown = coffee(150, 1, 7, years=10, annual_return=7)
    assert grown["invested"] > grown["projected_spend"], grown["invested"]
    assert grown["invested_gain"] > 0, grown["invested_gain"]
    assert abs(grown["opportunity"] - grown["invested"]) < 1e-9

    # Future-value annuity sanity: $100/mo at 12%/yr (1%/mo) for 1 year.
    # FV = 100 × ((1.01^12 − 1)/0.01) ≈ 1268.25
    fv = _future_value_annuity(100, 12, 1)
    assert abs(fv - 1268.250301) < 1e-3, fv
    assert _future_value_annuity(100, 0, 1) == 1200  # no return = sum of deposits
    assert _future_value_annuity(0, 7, 10) == 0
    assert _future_value_annuity(100, 7, 0) == 0

    # Verdict scales with the yearly number.
    assert coffee(0, 1, 7)["verdict"] == "No habit, no cost"
    assert coffee(150, 1, 7, annual_return=0)["verdict"] == "A holiday's worth, yearly"
    assert coffee(20, 1, 7, annual_return=0)["verdict"] == "Adds up quietly"  # ₹7,300/yr

    # Bad inputs.
    try:
        coffee(-5, 1, 7)
        assert False, "expected ValueError for negative price"
    except ValueError:
        pass

    # Clamping: absurd schedule values are pulled into range, not crashed on.
    c = coffee(150, 1, days_per_week=99, years=999)
    assert c["days_per_week"] == 7 and c["years"] == 100

    print("all checks passed")
