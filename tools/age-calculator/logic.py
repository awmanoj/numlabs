"""Age calculator — pure-Python logic.

Given a date of birth and a reference date (defaults to today), returns
the exact age as years/months/days and total days/weeks.
"""

from datetime import date


def age(birth_year, birth_month, birth_day, ref_year=None, ref_month=None, ref_day=None):
    """Return age breakdown between birth date and reference date.

    All args are ints. Reference date defaults to today when omitted.
    """
    dob = date(birth_year, birth_month, birth_day)

    if ref_year is None or ref_month is None or ref_day is None:
        today = date.today()
    else:
        today = date(ref_year, ref_month, ref_day)

    if dob > today:
        raise ValueError("Date of birth cannot be in the future")

    delta_days = (today - dob).days

    years = today.year - dob.year
    months = today.month - dob.month
    days = today.day - dob.day

    if days < 0:
        months -= 1
        # days remaining from the previous month
        prev_month = today.month - 1 if today.month > 1 else 12
        prev_year = today.year if today.month > 1 else today.year - 1
        days_in_prev = (date(prev_year, prev_month % 12 + 1, 1) - date(prev_year, prev_month, 1)).days
        days += days_in_prev

    if months < 0:
        years -= 1
        months += 12

    total_weeks = delta_days // 7
    remaining_days_after_weeks = delta_days % 7

    return {
        "years": years,
        "months": months,
        "days": days,
        "total_days": delta_days,
        "total_weeks": total_weeks,
        "remaining_days_after_weeks": remaining_days_after_weeks,
        "total_months": years * 12 + months,
    }


if __name__ == "__main__":
    from datetime import date as _date

    cases = [
        ((1990, 6, 15), (2026, 5, 24)),
        ((2000, 1, 1),  (2026, 5, 24)),
        ((1985, 12, 31), (2026, 5, 24)),
        ((2026, 5, 1),  (2026, 5, 24)),
    ]

    for dob_args, ref_args in cases:
        r = age(*dob_args, *ref_args)
        print(f"DOB {_date(*dob_args)}  →  "
              f"{r['years']}y {r['months']}m {r['days']}d  |  "
              f"{r['total_days']} days  |  "
              f"{r['total_weeks']} weeks + {r['remaining_days_after_weeks']} days  |  "
              f"{r['total_months']} months")
