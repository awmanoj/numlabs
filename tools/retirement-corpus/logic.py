"""Retirement corpus calculator — pure-Python logic.

Answers: *how much must I invest today, as a lump sum, so that I can draw a
chosen monthly income through retirement and have the pot last to a chosen
age?*

Model
-----
Returns are blended from an equity / debt split that can differ before and
after retirement::

    blended = equity_share·equity_return + (1 − equity_share)·debt_return

With the India-flavoured defaults (equity 14%, debt 6%, 100% equity before
retirement, 60% after) that's 14% accumulating and 10.8% drawing down.

The desired income defaults to **today's purchasing power**. It is inflated to
the retirement date, then grown by inflation every retirement year so the real
income stays flat.

Withdrawals happen at the **start** of each retirement year (annuity-due), from
the retirement age through the final age, inclusive. The corpus is sized so the
balance depletes to zero right after the last withdrawal:

    corpus_at_retirement = Σ_{k=0}^{N−1}  W₀·(1+g)^k / (1+r_post)^k
    corpus_today         = corpus_at_retirement / (1 + r_pre)^years_to_retire

where g is inflation, r_post the drawdown return, r_pre the accumulation return,
W₀ the first year's withdrawal and N the number of retirement years.

``plan`` returns the headline numbers, the assumptions, and a year-by-year
schedule (opening balance, withdrawal, returns earned, closing balance, net
change) that the page renders as a table and chart.
"""

import json


def blended_return(equity_share_pct, equity_pct, debt_pct):
    """Blend equity and debt nominal returns by an equity share. Returns a
    decimal rate (e.g. 0.108 for 10.8%)."""
    e = equity_share_pct / 100.0
    return (e * equity_pct + (1 - e) * debt_pct) / 100.0


def _check(cond, msg):
    if not cond:
        raise ValueError(msg)


def plan(monthly_income, current_age, retirement_age, final_age,
         equity_return=14.0, debt_return=6.0, inflation=7.0,
         equity_pre=100.0, equity_post=60.0, income_in_todays_money=True):
    """Compute the lump sum needed today plus a year-by-year schedule.

    Ages are whole years. ``monthly_income`` is the desired income; by default
    it is read in today's money and inflated to the retirement date.
    """
    _check(monthly_income > 0, "Monthly income must be positive")
    _check(current_age >= 0, "Current age can't be negative")
    _check(retirement_age >= current_age,
           "Retirement age must be at least your current age")
    _check(final_age >= retirement_age,
           "Final age must be at least the retirement age")
    for label, share in (("pre-retirement", equity_pre),
                         ("post-retirement", equity_post)):
        _check(0 <= share <= 100,
               f"Equity share ({label}) must be between 0 and 100%")
    _check(inflation > -100, "Inflation is out of range")

    r_pre = blended_return(equity_pre, equity_return, debt_return)
    r_post = blended_return(equity_post, equity_return, debt_return)
    g = inflation / 100.0

    years_acc = retirement_age - current_age
    n_w = final_age - retirement_age + 1          # inclusive of both ends

    annual_income_today = monthly_income * 12.0
    # First retirement year's withdrawal (nominal rupees at retirement).
    if income_in_todays_money:
        w0 = annual_income_today * (1 + g) ** years_acc
    else:
        w0 = annual_income_today

    # PV at retirement of the growing, start-of-year withdrawal stream.
    x = (1 + g) / (1 + r_post)
    if abs(x - 1) < 1e-12:
        corpus_at_retirement = w0 * n_w
    else:
        corpus_at_retirement = w0 * (1 - x ** n_w) / (1 - x)

    corpus_today = corpus_at_retirement / (1 + r_pre) ** years_acc

    # ── year-by-year simulation ──
    schedule = []
    balance = corpus_today
    total_withdrawn = 0.0
    for age in range(current_age, final_age + 1):
        opening = balance
        if age < retirement_age:
            withdrawal = 0.0
            rate = r_pre
            phase = "accumulate"
        else:
            k = age - retirement_age
            withdrawal = w0 * (1 + g) ** k
            rate = r_post
            phase = "withdraw"
        after_wd = opening - withdrawal
        returns = after_wd * rate
        closing = after_wd + returns
        total_withdrawn += withdrawal
        schedule.append({
            "age": age,
            "phase": phase,
            "opening": opening,
            "withdrawal": withdrawal,
            "returns": returns,
            "closing": closing,
            "net": closing - opening,
        })
        balance = closing

    # Floating drift only; snap a near-zero final balance to exactly zero.
    if schedule and abs(schedule[-1]["closing"]) < max(1.0, corpus_today * 1e-9):
        schedule[-1]["closing"] = 0.0
        schedule[-1]["net"] = schedule[-1]["closing"] - schedule[-1]["opening"]

    return {
        "summary": {
            "corpus_today": corpus_today,
            "corpus_at_retirement": corpus_at_retirement,
            "first_year_annual": w0,
            "first_year_monthly": w0 / 12.0,
            "last_year_annual": w0 * (1 + g) ** (n_w - 1),
            "last_year_monthly": w0 * (1 + g) ** (n_w - 1) / 12.0,
            "total_withdrawn": total_withdrawn,
            "years_accumulation": years_acc,
            "years_retirement": n_w,
        },
        "assumptions": {
            "r_pre_pct": round(r_pre * 100, 2),
            "r_post_pct": round(r_post * 100, 2),
            "equity_return": equity_return,
            "debt_return": debt_return,
            "inflation": inflation,
            "equity_pre": equity_pre,
            "equity_post": equity_post,
            "income_in_todays_money": income_in_todays_money,
        },
        "schedule": schedule,
    }


def plan_json(monthly_income, current_age, retirement_age, final_age,
              equity_return, debt_return, inflation,
              equity_pre, equity_post, income_in_todays_money):
    return json.dumps(plan(
        monthly_income, current_age, retirement_age, final_age,
        equity_return, debt_return, inflation,
        equity_pre, equity_post, income_in_todays_money))


if __name__ == "__main__":
    # Blended returns
    assert abs(blended_return(100, 14, 6) - 0.14) < 1e-12
    assert abs(blended_return(60, 14, 6) - 0.108) < 1e-12
    assert abs(blended_return(0, 14, 6) - 0.06) < 1e-12

    # Headline scenario: ₹1L/month today, retire 60, draw to 85.
    p = plan(100000, 30, 60, 85)
    s = p["summary"]
    print(f"corpus today        : {s['corpus_today']:,.0f}")
    print(f"corpus at retirement: {s['corpus_at_retirement']:,.0f}")
    print(f"first-yr monthly w/d : {s['first_year_monthly']:,.0f}")
    print(f"last-yr monthly w/d  : {s['last_year_monthly']:,.0f}")
    print(f"total withdrawn      : {s['total_withdrawn']:,.0f}")
    print(f"blended pre/post     : {p['assumptions']['r_pre_pct']}% / "
          f"{p['assumptions']['r_post_pct']}%")

    sched = p["schedule"]
    # One row per age, inclusive
    assert len(sched) == 85 - 30 + 1
    assert sched[0]["age"] == 30 and sched[-1]["age"] == 85
    # Accumulation has no withdrawals; retirement does
    assert sched[0]["withdrawal"] == 0
    assert sched[30]["age"] == 60 and sched[30]["withdrawal"] > 0
    # Portfolio depletes by the final age
    assert sched[-1]["closing"] == 0.0, sched[-1]["closing"]
    # Balance at retirement matches the closed form
    assert abs(sched[30]["opening"] - s["corpus_at_retirement"]) < 1.0
    # Within each accumulation year, growth = opening * r_pre
    assert abs(sched[0]["returns"] - sched[0]["opening"] * 0.14) < 1e-6
    # Withdrawals grow with inflation
    assert abs(sched[31]["withdrawal"] / sched[30]["withdrawal"] - 1.07) < 1e-9

    # income_in_todays_money=False uses the income as-is at retirement
    p2 = plan(100000, 30, 60, 85, income_in_todays_money=False)
    assert abs(p2["summary"]["first_year_annual"] - 1_200_000) < 1e-6

    # Retire-now edge: no accumulation phase
    p3 = plan(50000, 60, 60, 80)
    assert p3["summary"]["years_accumulation"] == 0
    assert abs(p3["summary"]["corpus_today"]
               - p3["summary"]["corpus_at_retirement"]) < 1e-6
    assert p3["schedule"][0]["age"] == 60

    # Inflation == post-return → geometric series degenerates to N·W0 (x==1)
    p4 = plan(100000, 59, 60, 64, inflation=10.8, equity_post=60,
              equity_return=14, debt_return=6)
    # 5 retirement years, PV uses N·W0 at retirement
    assert p4["summary"]["years_retirement"] == 5

    # JSON path the browser uses
    payload = json.loads(plan_json(100000, 30, 60, 85, 14, 6, 7, 100, 60, True))
    assert "schedule" in payload and len(payload["schedule"]) == 56

    # Errors
    for kwargs in (
        dict(monthly_income=0, current_age=30, retirement_age=60, final_age=85),
        dict(monthly_income=1000, current_age=40, retirement_age=35, final_age=85),
        dict(monthly_income=1000, current_age=30, retirement_age=60, final_age=55),
        dict(monthly_income=1000, current_age=30, retirement_age=60, final_age=85,
             equity_pre=140),
    ):
        try:
            plan(**kwargs)
            raise AssertionError(f"expected failure for {kwargs}")
        except ValueError as e:
            print(f"rejected: {e}")

    print("all checks passed")
