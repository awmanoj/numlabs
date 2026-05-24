"""Loan EMI — pure-Python logic.

EMI (Equated Monthly Installment) for a fixed-rate amortizing loan.

    EMI = P · r · (1 + r)^n / ((1 + r)^n − 1)

r is the monthly rate (annual rate / 12 / 100); n is the number of months.
"""


def loan_emi(principal, annual_rate_percent, years):
    """Return EMI plus a year-by-year amortization summary.

    The schedule aggregates monthly payments into yearly rows
    (principal paid this year, interest paid this year, remaining balance).
    """
    months = round(years * 12)
    r = annual_rate_percent / 100 / 12

    if r == 0:
        emi = principal / months
    else:
        emi = principal * r * (1 + r) ** months / ((1 + r) ** months - 1)

    schedule = []
    balance = principal
    year_principal = 0.0
    year_interest = 0.0
    for m in range(1, months + 1):
        interest = balance * r
        principal_paid = emi - interest
        balance -= principal_paid
        year_principal += principal_paid
        year_interest += interest
        if m % 12 == 0 or m == months:
            schedule.append({
                "year": (m + 11) // 12,
                "principal": round(year_principal, 2),
                "interest": round(year_interest, 2),
                "balance": round(max(balance, 0), 2),
            })
            year_principal = 0.0
            year_interest = 0.0

    total_payment = emi * months
    return {
        "emi": round(emi, 2),
        "total_payment": round(total_payment, 2),
        "total_interest": round(total_payment - principal, 2),
        "schedule": schedule,
    }


if __name__ == "__main__":
    r = loan_emi(500_000, 8, 20)
    print(f"EMI:            ${r['emi']:,.2f}/month")
    print(f"Total payment:  ${r['total_payment']:,.2f}")
    print(f"Total interest: ${r['total_interest']:,.2f}")
    print(f"Year 1:  principal ${r['schedule'][0]['principal']:>11,.2f}  "
          f"interest ${r['schedule'][0]['interest']:>11,.2f}  "
          f"balance ${r['schedule'][0]['balance']:>11,.2f}")
    print(f"Year {r['schedule'][-1]['year']:>2}: principal ${r['schedule'][-1]['principal']:>11,.2f}  "
          f"interest ${r['schedule'][-1]['interest']:>11,.2f}  "
          f"balance ${r['schedule'][-1]['balance']:>11,.2f}")
