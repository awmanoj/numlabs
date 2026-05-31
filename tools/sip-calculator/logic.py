"""SIP (Systematic Investment Plan) calculator — pure-Python logic.

Invest a fixed amount at the *start* of every month for `years`, compounding
monthly at an expected annual rate of return. Returns the maturity value
(corpus), the total invested, and the estimated gains, plus a year-by-year
breakdown.

SIP uses beginning-of-month contributions (an annuity due), so each deposit
earns one extra month of growth versus an end-of-month annuity. Closed form
when there is no step-up:

    FV = P · ((1 + i)^n − 1) / i · (1 + i)

where i is the monthly rate (annual / 12) and n is the number of months.

An optional annual `step_up_percent` raises the monthly amount once a year —
a "top-up" or step-up SIP — which the closed form can't express, so the
breakdown is built by month-by-month simulation that handles both cases.
"""

MONTHS_PER_YEAR = 12


def sip(monthly_investment, annual_return_percent, years, step_up_percent=0):
    """Future value of a monthly SIP, with optional annual step-up.

    monthly_investment   — amount invested at the start of each month
    annual_return_percent — expected annual return (%), compounded monthly
    years                — investment horizon in whole years
    step_up_percent      — annual increase applied to the monthly amount (%)
    """
    i = annual_return_percent / 100 / MONTHS_PER_YEAR
    n = years * MONTHS_PER_YEAR
    step = step_up_percent / 100

    balance = 0.0
    invested = 0.0
    amount = monthly_investment
    breakdown = []

    for m in range(1, n + 1):
        # Beginning-of-month contribution, then a month of growth.
        balance += amount
        invested += amount
        balance *= (1 + i)

        if m % MONTHS_PER_YEAR == 0:
            breakdown.append({
                "year": m // MONTHS_PER_YEAR,
                "invested": round(invested, 2),
                "value": round(balance, 2),
                "gains": round(balance - invested, 2),
            })
            # Step up the contribution for the coming year.
            amount *= (1 + step)

    return {
        "future_value": round(balance, 2),
        "total_invested": round(invested, 2),
        "estimated_returns": round(balance - invested, 2),
        "breakdown": breakdown,
    }


if __name__ == "__main__":
    print("SIP: 10,000/month at 12% for 20 years")
    s = sip(10_000, 12, 20)
    print(f"  Maturity value:    {s['future_value']:,.2f}")
    print(f"  Total invested:    {s['total_invested']:,.2f}")
    print(f"  Estimated returns: {s['estimated_returns']:,.2f}")

    # Cross-check the no-step-up case against the closed form.
    P, rate, yrs = 10_000, 12, 20
    i = rate / 100 / 12
    n = yrs * 12
    closed = P * ((1 + i) ** n - 1) / i * (1 + i)
    assert abs(closed - s["future_value"]) < 0.01, (closed, s["future_value"])

    # Zero-rate SIP is just the sum of contributions.
    z = sip(5_000, 0, 3)
    assert z["future_value"] == z["total_invested"] == 5_000 * 36, z

    print()
    print("STEP-UP SIP: 10,000/month at 12% for 20 years, 10% annual step-up")
    su = sip(10_000, 12, 20, step_up_percent=10)
    print(f"  Maturity value:    {su['future_value']:,.2f}")
    print(f"  Total invested:    {su['total_invested']:,.2f}")
    print(f"  Estimated returns: {su['estimated_returns']:,.2f}")
    assert su["future_value"] > s["future_value"]

    print("\nOK")
