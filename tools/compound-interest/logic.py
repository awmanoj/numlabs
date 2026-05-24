"""Compound interest — pure-Python logic.

Runs unchanged in CPython and in the browser via Pyodide.
"""

import math


def compound_interest(principal, annual_rate_percent, years, periods_per_year):
    """Future value of `principal` compounded for `years` years.

    principal:            starting amount (any currency)
    annual_rate_percent:  nominal annual interest rate, e.g. 5 for 5%
    years:                time horizon in years (int or float)
    periods_per_year:     compounding frequency; use 0 for continuous compounding

    Returns a dict:
        final_amount    — value after `years`
        total_interest  — final_amount - principal
        breakdown       — list of {year, amount, interest}, sampled to ~25 rows max
    """
    r = annual_rate_percent / 100

    def value_at(t):
        if periods_per_year == 0:
            return principal * math.exp(r * t)
        n = periods_per_year
        return principal * (1 + r / n) ** (n * t)

    final = value_at(years)

    # Sample the timeline so the table never grows beyond ~25 rows.
    step = 1 if years <= 25 else max(1, round(years / 25))
    breakdown = []
    t = step
    while t < years:
        amt = value_at(t)
        breakdown.append({
            "year": t,
            "amount": round(amt, 2),
            "interest": round(amt - principal, 2),
        })
        t += step
    breakdown.append({
        "year": years,
        "amount": round(final, 2),
        "interest": round(final - principal, 2),
    })

    return {
        "final_amount": round(final, 2),
        "total_interest": round(final - principal, 2),
        "breakdown": breakdown,
    }


if __name__ == "__main__":
    # Sanity check: $1,000 at 5% APR over 10 years, compounded monthly.
    result = compound_interest(1000, 5, 10, 12)
    print(f"Final amount:   ${result['final_amount']:,.2f}")
    print(f"Total interest: ${result['total_interest']:,.2f}")
    print("Year-by-year:")
    for row in result["breakdown"]:
        print(f"  year {row['year']:>2}: ${row['amount']:>10,.2f}  (+${row['interest']:,.2f})")
