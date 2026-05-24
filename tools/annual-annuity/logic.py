"""Annual annuity — pure-Python logic.

Two modes:
  save     — deposit `payment` at the end of each year; return future value.
  withdraw — start with `principal`; return the level annual payout that
             exhausts the corpus over `years` years.

    FV  = PMT · ((1 + r)^n − 1) / r
    PMT = PV  · r / (1 − (1 + r)^−n)
"""

PERIODS_PER_YEAR = 1


def annuity_save(payment, annual_rate_percent, years):
    """Future value of a recurring deposit, plus year-by-year balance."""
    r = annual_rate_percent / 100 / PERIODS_PER_YEAR
    n = years * PERIODS_PER_YEAR

    if r == 0:
        fv = payment * n
    else:
        fv = payment * (((1 + r) ** n - 1) / r)

    breakdown = []
    balance = 0.0
    contributed = 0.0
    for p in range(1, n + 1):
        interest = balance * r
        balance += interest + payment
        contributed += payment
        if p % PERIODS_PER_YEAR == 0:
            breakdown.append({
                "year": p // PERIODS_PER_YEAR,
                "balance": round(balance, 2),
                "contributed": round(contributed, 2),
                "interest": round(balance - contributed, 2),
            })

    return {
        "future_value": round(fv, 2),
        "total_contributions": round(payment * n, 2),
        "interest_earned": round(fv - payment * n, 2),
        "breakdown": breakdown,
    }


def annuity_withdraw(principal, annual_rate_percent, years):
    """Level annual payout that drains the corpus, plus remaining balance."""
    r = annual_rate_percent / 100 / PERIODS_PER_YEAR
    n = years * PERIODS_PER_YEAR

    if r == 0:
        pmt = principal / n
    else:
        pmt = principal * r / (1 - (1 + r) ** -n)

    breakdown = []
    balance = principal
    withdrawn = 0.0
    for p in range(1, n + 1):
        interest = balance * r
        balance += interest - pmt
        withdrawn += pmt
        if p % PERIODS_PER_YEAR == 0:
            breakdown.append({
                "year": p // PERIODS_PER_YEAR,
                "balance": round(max(balance, 0), 2),
                "withdrawn": round(withdrawn, 2),
            })

    return {
        "periodic_payout": round(pmt, 2),
        "total_received": round(pmt * n, 2),
        "interest_received": round(pmt * n - principal, 2),
        "breakdown": breakdown,
    }


if __name__ == "__main__":
    print("SAVE: $10,000/year at 6% for 20 years")
    s = annuity_save(10_000, 6, 20)
    print(f"  Future value:       ${s['future_value']:,.2f}")
    print(f"  Total contributed:  ${s['total_contributions']:,.2f}")
    print(f"  Interest earned:    ${s['interest_earned']:,.2f}")
    print()
    print("WITHDRAW: $500,000 corpus at 6% for 20 years")
    w = annuity_withdraw(500_000, 6, 20)
    print(f"  Annual payout:      ${w['periodic_payout']:,.2f}")
    print(f"  Total received:     ${w['total_received']:,.2f}")
    print(f"  Interest received:  ${w['interest_received']:,.2f}")
