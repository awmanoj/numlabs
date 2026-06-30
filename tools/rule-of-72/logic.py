"""Rule of 72 — how long money takes to double, triple, or multiply.

Pure-Python logic. Runs unchanged in CPython and in the browser via Pyodide.

The Rule of 72 is the back-of-the-envelope trick: years-to-double ≈ 72 / rate%.
This module pairs that shortcut with the *exact* answer from compound growth,
and generalises it — the magic number for any target multiple m is

    rule_number(m) = 72 · log2(m)

so doubling uses 72, tripling ≈ 114, quadrupling = 144. It also runs the math
backwards (what rate doubles my money in N years?) and forwards (how many times
does my money multiply in N years?).
"""

import math


def _per_period_growth(rate_percent, periods_per_year):
    """Growth factor of one compounding period, e.g. 1.00583 for 7%/12.

    periods_per_year = 0 is treated by the callers as continuous compounding,
    so it is never passed here.
    """
    return 1 + (rate_percent / 100) / periods_per_year


def exact_time(rate_percent, multiple, periods_per_year=1):
    """Exact years for a sum to grow by `multiple` at `rate_percent` a year.

    multiple:          target growth, e.g. 2 for doubling, 10 for ten-fold
    periods_per_year:  compounding frequency; use 0 for continuous compounding

    Solves multiple = (1 + r/n)^(n·t)  →  t = ln(multiple) / (n·ln(1 + r/n)).
    Continuous case: multiple = e^(r·t) → t = ln(multiple) / r.
    """
    if multiple <= 1:
        raise ValueError("multiple must be greater than 1")
    if rate_percent <= 0:
        raise ValueError("rate must be positive for money to grow")

    r = rate_percent / 100
    if periods_per_year == 0:
        return math.log(multiple) / r
    n = periods_per_year
    return math.log(multiple) / (n * math.log(1 + r / n))


def rule_number(multiple, rule_base=72):
    """The 'magic number' for a target multiple: rule_base · log2(multiple).

    Doubling → 72, tripling → ≈114.0, quadrupling → 144. Swap rule_base for
    70 (cleaner division) or 69.3 (exact for continuous compounding, = 100·ln2).
    """
    return rule_base * math.log2(multiple)


def rule_estimate_time(rate_percent, multiple=2, rule_base=72):
    """The shortcut estimate: rule_number(multiple) / rate%.

    No compounding frequency — that's the whole point of the trick.
    """
    if rate_percent <= 0:
        raise ValueError("rate must be positive for money to grow")
    return rule_number(multiple, rule_base) / rate_percent


def exact_rule_number(rate_percent, multiple=2, periods_per_year=1):
    """The rule number that would be *exact* at this rate: rate% · exact_time.

    At 8% annual this lands near 72 for doubling — which is why 72 is the
    number everyone memorises. Away from ~8% the true value drifts.
    """
    return rate_percent * exact_time(rate_percent, multiple, periods_per_year)


def required_rate(multiple, years, periods_per_year=1):
    """Annual rate% needed to grow by `multiple` within `years`.

    The inverse of exact_time. Continuous: r = ln(multiple)/years.
    Discrete: nominal annual rate = n·((multiple)^(1/(n·years)) − 1).
    """
    if multiple <= 1:
        raise ValueError("multiple must be greater than 1")
    if years <= 0:
        raise ValueError("years must be positive")

    if periods_per_year == 0:
        return 100 * math.log(multiple) / years
    n = periods_per_year
    per_period = multiple ** (1 / (n * years)) - 1
    return 100 * n * per_period


def multiple_after(rate_percent, years, periods_per_year=1):
    """How many times the money multiplies after `years` (1.0 = unchanged)."""
    r = rate_percent / 100
    if periods_per_year == 0:
        return math.exp(r * years)
    n = periods_per_year
    return (1 + r / n) ** (n * years)


def amount_after(principal, rate_percent, years, periods_per_year=1):
    """Value of `principal` after `years` at `rate_percent`."""
    return principal * multiple_after(rate_percent, years, periods_per_year)


def milestones(rate_percent, principal=1, periods_per_year=1,
               multiples=(2, 3, 4, 5, 10)):
    """Per-multiple table: exact years, rule estimate, and resulting amount.

    Each row is {multiple, exact_years, rule_years, amount}. The rule estimate
    uses the classic base 72 so the table doubles as an accuracy comparison.
    """
    rows = []
    for m in multiples:
        ey = exact_time(rate_percent, m, periods_per_year)
        rows.append({
            "multiple": m,
            "exact_years": round(ey, 2),
            "rule_years": round(rule_estimate_time(rate_percent, m), 2),
            "amount": round(principal * m, 2),
        })
    return rows


def classify(rate_percent, multiple=2, periods_per_year=1):
    """Compare the shortcut against the exact answer and grade its accuracy.

    Returns exact/estimate years, their gap, and a plain-English verdict on how
    well the Rule of 72 holds at this rate.
    """
    exact = exact_time(rate_percent, multiple, periods_per_year)
    estimate = rule_estimate_time(rate_percent, multiple)
    diff = estimate - exact
    rel = abs(diff) / exact

    if rel < 0.01:
        verdict = "spot on — the Rule of 72 is essentially exact here"
    elif rel < 0.03:
        verdict = "very close — the shortcut is well within a rounding error"
    elif rel < 0.07:
        verdict = "close enough for mental math, off by a fraction of a year"
    else:
        verdict = "rough — far from the ~8% sweet spot, so trust the exact figure"

    return {
        "exact_years": round(exact, 2),
        "estimate_years": round(estimate, 2),
        "diff_years": round(diff, 2),
        "percent_error": round(100 * rel, 2),
        "verdict": verdict,
    }


if __name__ == "__main__":
    # Sanity check: at 8% the Rule of 72 should nearly nail the doubling time.
    c = classify(8, 2, 1)
    assert abs(c["exact_years"] - 9.01) < 0.05, c
    assert c["percent_error"] < 1, c
    print(f"At 8%/yr: doubles in {c['exact_years']} yrs "
          f"(rule of 72 says {c['estimate_years']}) — {c['verdict']}")

    # rule_number generalisation: tripling ≈ 114, quadrupling = 144.
    assert abs(rule_number(3) - 114.13) < 0.1, rule_number(3)
    assert abs(rule_number(4) - 144) < 1e-9, rule_number(4)

    # Inverse should round-trip: rate that doubles in exact_time(2) is the rate.
    t = exact_time(6, 2, 12)
    assert abs(required_rate(2, t, 12) - 6) < 1e-6
    print(f"At 6%/yr (monthly): doubles in {round(t, 2)} yrs")

    # multiple_after / amount_after consistency.
    assert abs(amount_after(1000, 7, 10, 12) - 2009.66) < 0.5

    print("\nMilestones at 7%/yr, $1,000 principal, annual compounding:")
    for row in milestones(7, principal=1000):
        print(f"  {row['multiple']:>2}×: exact {row['exact_years']:>5} yrs "
              f"(rule {row['rule_years']:>5}) → ${row['amount']:,.0f}")
