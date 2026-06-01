"""Freelance rate — pure-Python logic.

Going freelance, the first hard question is "what do I charge an hour?" The
naive answer — take a salary, divide by 2,080 hours — is a trap: it ignores the
weeks you don't work, the hours you can't bill (sales, admin, email), the
business costs an employer used to cover, and the tax an employer used to
withhold. Do that, and you quietly earn far less than the salaried job you left.

This works the sum backwards from the income you actually want to keep:

  * Start with your **salary goal** — the income you want for yourself — and add
    your annual **business expenses** (software, hardware, insurance, accounting).
    That's what the business has to clear before tax.
  * Gross that up for **tax** (income + self-employment), since the rate has to
    cover the tax too: ``gross = (goal + expenses) / (1 - tax)``.
  * Count the hours you can actually sell. Of the year's 52 weeks, subtract the
    **weeks off** (holidays, vacation, sick) to get working weeks. Of each
    week's working hours, only a **billable fraction** reaches a client — the
    rest is running the business. So
    ``billable hours/yr = hours/week × billable% × working weeks``.
  * The rate is the one divided by the other:
    ``hourly = gross / billable hours``.

From the hourly rate everything else follows — a day rate (a 5-day week split),
a week rate, and the monthly revenue the business needs to bring in. It's a
starting point for a quote, not a market price: charge what the work is worth,
but never below the floor this sets.
"""

# A year is ~52.14 weeks; 52 is the number everyone reasons with, so use it.
_WEEKS_PER_YEAR = 52.0
_DAYS_PER_WEEK = 5.0       # a standard billable working week
_MONTHS_PER_YEAR = 12.0

# Sane bounds so a stray value can't produce nonsense.
_MIN_WEEKS_OFF = 0.0
_MAX_WEEKS_OFF = 51.0      # leave at least one working week
_MAX_TAX_PCT = 95.0        # gross-up stays finite


def _num(x, default=0.0):
    """Coerce to float, falling back to ``default`` on junk input."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return default
    if v != v:  # NaN
        return default
    return v


def _verdict(billable_pct):
    """A plain-language read on how realistic the billable assumption is.

    Most freelancers can't bill anywhere near 100% of their working hours —
    selling, admin, and email eat a real share. The bands flag when the input
    is rosy enough that the rate it produces is probably too low to hit in
    practice.
    """
    if billable_pct >= 90:
        return "Optimistic — few bill this much"
    if billable_pct >= 70:
        return "Healthy utilization"
    if billable_pct >= 50:
        return "Realistic utilization"
    return "Lots of unbilled time"


def freelance(salary_goal, annual_expenses=0, weeks_off=6,
              hours_per_week=40, billable_pct=70, tax_pct=25):
    """Hourly rate needed to clear ``salary_goal`` after costs and tax.

    ``salary_goal`` is the income you want to keep for yourself;
    ``annual_expenses`` is what the business spends a year. ``weeks_off`` is the
    non-working weeks (subtracted from 52). ``hours_per_week`` is total working
    hours, of which ``billable_pct`` percent actually reach a client.
    ``tax_pct`` grosses the target up so the rate covers tax too.

    Returns a dict of raw numbers and supporting metrics; raises ``ValueError``
    when the inputs leave no billable hours to spread the target across.
    """
    salary_goal = _num(salary_goal)
    annual_expenses = _num(annual_expenses, 0)
    weeks_off = max(_MIN_WEEKS_OFF, min(_MAX_WEEKS_OFF, _num(weeks_off, 6)))
    hours_per_week = max(0.0, _num(hours_per_week, 40))
    billable_pct = max(0.0, min(100.0, _num(billable_pct, 70)))
    tax_pct = max(0.0, min(_MAX_TAX_PCT, _num(tax_pct, 25)))

    if salary_goal < 0:
        raise ValueError("Salary goal can't be negative.")
    if annual_expenses < 0:
        raise ValueError("Expenses can't be negative.")

    working_weeks = _WEEKS_PER_YEAR - weeks_off
    billable_hours_week = hours_per_week * billable_pct / 100.0
    billable_hours_year = billable_hours_week * working_weeks

    if billable_hours_year <= 0:
        raise ValueError("No billable hours — check hours, billable %, and weeks off.")

    # The business must clear goal + expenses *after* tax, so gross it up.
    after_tax_target = salary_goal + annual_expenses
    gross_needed = after_tax_target / (1.0 - tax_pct / 100.0)

    hourly_rate = gross_needed / billable_hours_year
    day_rate = hourly_rate * (billable_hours_week / _DAYS_PER_WEEK)
    week_rate = hourly_rate * billable_hours_week
    month_revenue = gross_needed / _MONTHS_PER_YEAR

    return {
        "salary_goal": salary_goal,
        "annual_expenses": annual_expenses,
        "weeks_off": weeks_off,
        "hours_per_week": hours_per_week,
        "billable_pct": billable_pct,
        "tax_pct": tax_pct,
        "working_weeks": working_weeks,
        "billable_hours_week": billable_hours_week,
        "billable_hours_year": billable_hours_year,
        "after_tax_target": after_tax_target,
        "gross_needed": gross_needed,
        "tax_amount": gross_needed - after_tax_target,
        "hourly_rate": hourly_rate,
        "day_rate": day_rate,
        "week_rate": week_rate,
        "month_revenue": month_revenue,
        "verdict": _verdict(billable_pct),
    }


if __name__ == "__main__":
    # Headline example: want to keep $80k, $5k expenses, 6 weeks off, 40 h/week,
    # 70% billable, 25% tax.
    r = freelance(80000, 5000, 6, 40, 70, 25)
    weeks = 52 - 6                       # 46 working weeks
    bhw = 40 * 0.70                      # 28 billable hours/week
    bhy = bhw * weeks                    # 1288 billable hours/year
    gross = (80000 + 5000) / (1 - 0.25)  # 113,333.33
    assert abs(r["working_weeks"] - weeks) < 1e-9, r["working_weeks"]
    assert abs(r["billable_hours_week"] - bhw) < 1e-9, r["billable_hours_week"]
    assert abs(r["billable_hours_year"] - bhy) < 1e-9, r["billable_hours_year"]
    assert abs(r["gross_needed"] - gross) < 1e-6, r["gross_needed"]
    assert abs(r["hourly_rate"] - gross / bhy) < 1e-6, r["hourly_rate"]
    assert abs(r["tax_amount"] - (gross - 85000)) < 1e-6, r["tax_amount"]

    # Day rate is the hourly rate over a billable day (week split 5 ways);
    # week rate is the hourly rate over a billable week.
    assert abs(r["day_rate"] - r["hourly_rate"] * (bhw / 5)) < 1e-9, r["day_rate"]
    assert abs(r["week_rate"] - r["hourly_rate"] * bhw) < 1e-9, r["week_rate"]
    assert abs(r["month_revenue"] - gross / 12) < 1e-6, r["month_revenue"]

    # No tax and no expenses: gross equals the salary goal exactly.
    flat = freelance(50000, 0, 0, 50, 100, 0)
    assert abs(flat["gross_needed"] - 50000) < 1e-9, flat["gross_needed"]
    assert abs(flat["tax_amount"]) < 1e-9, flat["tax_amount"]
    # 52 weeks × 50 h × 100% = 2600 billable hours → $19.23/h.
    assert abs(flat["billable_hours_year"] - 2600) < 1e-9, flat["billable_hours_year"]
    assert abs(flat["hourly_rate"] - 50000 / 2600) < 1e-9, flat["hourly_rate"]

    # Higher tax raises the gross and therefore the rate.
    lo = freelance(80000, 0, 6, 40, 70, 0)
    hi = freelance(80000, 0, 6, 40, 70, 40)
    assert hi["hourly_rate"] > lo["hourly_rate"], (lo["hourly_rate"], hi["hourly_rate"])
    assert abs(hi["gross_needed"] - 80000 / 0.6) < 1e-6, hi["gross_needed"]

    # Fewer billable hours → higher rate to hit the same goal.
    fewer = freelance(80000, 5000, 12, 40, 50, 25)
    assert fewer["hourly_rate"] > r["hourly_rate"], fewer["hourly_rate"]

    # Verdict tracks the billable percentage.
    assert freelance(80000, 0, 6, 40, 95, 25)["verdict"] == "Optimistic — few bill this much"
    assert freelance(80000, 0, 6, 40, 70, 25)["verdict"] == "Healthy utilization"
    assert freelance(80000, 0, 6, 40, 55, 25)["verdict"] == "Realistic utilization"
    assert freelance(80000, 0, 6, 40, 30, 25)["verdict"] == "Lots of unbilled time"

    # Clamping: absurd values are pulled into range, not crashed on.
    c = freelance(80000, 0, weeks_off=99, hours_per_week=40, billable_pct=200, tax_pct=300)
    assert c["weeks_off"] == 51 and c["billable_pct"] == 100 and c["tax_pct"] == 95

    # Bad inputs.
    try:
        freelance(-1)
        assert False, "expected ValueError for negative goal"
    except ValueError:
        pass

    # No billable hours at all is an error, not a divide-by-zero.
    try:
        freelance(80000, 0, 6, 0, 70, 25)
        assert False, "expected ValueError for zero hours"
    except ValueError:
        pass

    print("all checks passed")
