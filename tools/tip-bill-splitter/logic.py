"""Tip & bill splitter.

Given a bill amount, a tip percentage and the number of people sharing the
check, compute the tip, the grand total, and what each person owes. Everything
is currency-agnostic — the numbers work the same whether you're paying in
dollars, euros, rupees or pebbles.

An optional rounding step makes each person's share land on a clean number
(e.g. the nearest whole unit, or the next 0.50 up). Rounding the *per-person*
share changes the real total paid, so we report the adjusted total, the extra
left on the table, and the effective tip percentage that rounding works out to.
"""

import math

EPS = 1e-9


def _round_to(x, inc, direction):
    """Round x to the nearest multiple of `inc` in the given direction.

    direction is "up", "down" or "nearest". A tiny epsilon keeps values that
    are already on a multiple (e.g. 12.00 to the nearest 0.50) from being
    nudged to the next step by floating-point fuzz.
    """
    if inc <= 0:
        return x
    q = x / inc
    if direction == "up":
        q = math.ceil(q - EPS)
    elif direction == "down":
        q = math.floor(q + EPS)
    else:  # nearest
        q = math.floor(q + 0.5)
    return q * inc


def split(bill, tip_percent, people, round_to=0.0, round_dir="up"):
    if bill is None or tip_percent is None or people is None:
        raise ValueError("Enter the bill, tip percentage and number of people")

    bill = float(bill)
    tip_percent = float(tip_percent)
    people = int(people)
    round_to = float(round_to)

    if bill < 0:
        raise ValueError("Bill amount can't be negative")
    if tip_percent < 0:
        raise ValueError("Tip percentage can't be negative")
    if people < 1:
        raise ValueError("Need at least one person to split between")
    if round_dir not in ("up", "down", "nearest"):
        raise ValueError("round_dir must be 'up', 'down' or 'nearest'")

    tip = bill * tip_percent / 100.0
    total = bill + tip
    per_person = total / people

    out = {
        "bill": bill,
        "tip_percent": tip_percent,
        "people": people,
        "tip": tip,
        "total": total,
        "per_person": per_person,
        "per_person_bill": bill / people,
        "per_person_tip": tip / people,
        "rounded": False,
    }

    if round_to > 0:
        rounded_per_person = _round_to(per_person, round_to, round_dir)
        rounded_total = rounded_per_person * people
        adjustment = rounded_total - total
        # Effective tip = whatever sits on top of the bill once rounding lands.
        effective_tip = rounded_total - bill
        effective_pct = (effective_tip / bill * 100.0) if bill > EPS else 0.0
        out.update(
            {
                "rounded": True,
                "round_to": round_to,
                "round_dir": round_dir,
                "rounded_per_person": rounded_per_person,
                "rounded_total": rounded_total,
                "adjustment": adjustment,
                "effective_tip": effective_tip,
                "effective_tip_percent": effective_pct,
            }
        )

    return out


if __name__ == "__main__":
    # Plain split: 100 bill, 20% tip, 4 people.
    r = split(100, 20, 4)
    assert math.isclose(r["tip"], 20.0)
    assert math.isclose(r["total"], 120.0)
    assert math.isclose(r["per_person"], 30.0)
    assert math.isclose(r["per_person_tip"], 5.0)
    assert not r["rounded"]
    print(f"100 @ 20% / 4 → {r['per_person']:.2f} each, total {r['total']:.2f}")

    # Decimal bill and tip: 53.70 @ 18% between 3.
    r = split(53.70, 18, 3)
    assert math.isclose(r["tip"], 53.70 * 0.18)
    assert math.isclose(r["total"], 53.70 * 1.18)
    assert math.isclose(r["per_person"], 53.70 * 1.18 / 3)
    print(f"53.70 @ 18% / 3 → {r['per_person']:.4f} each")

    # Round each share UP to the next whole unit.
    r = split(85.50, 15, 4, round_to=1, round_dir="up")
    raw = 85.50 * 1.15 / 4  # ≈ 24.58
    assert math.isclose(r["per_person"], raw)
    assert math.isclose(r["rounded_per_person"], 25.0)
    assert math.isclose(r["rounded_total"], 100.0)
    assert r["adjustment"] > 0
    assert math.isclose(r["effective_tip"], 100.0 - 85.50)
    print(f"85.50 @ 15% / 4 → round up to {r['rounded_per_person']:.2f} each, "
          f"effective tip {r['effective_tip_percent']:.1f}%")

    # Round to the nearest 0.50.
    r = split(47.30, 20, 2, round_to=0.5, round_dir="nearest")
    raw = 47.30 * 1.20 / 2  # 28.38
    assert math.isclose(r["per_person"], raw)
    assert math.isclose(r["rounded_per_person"], 28.5), r["rounded_per_person"]
    print(f"47.30 @ 20% / 2 → nearest 0.50 = {r['rounded_per_person']:.2f} each")

    # Round DOWN — shortchanges the tip a touch.
    r = split(60, 18, 3, round_to=1, round_dir="down")
    raw = 60 * 1.18 / 3  # 23.6
    assert math.isclose(r["rounded_per_person"], 23.0)
    assert r["adjustment"] < 0
    print(f"60 @ 18% / 3 → round down to {r['rounded_per_person']:.2f} each")

    # Already on a multiple — epsilon must not bump it up.
    r = split(100, 20, 4, round_to=0.5, round_dir="up")
    assert math.isclose(r["rounded_per_person"], 30.0), r["rounded_per_person"]
    print("30.00 already on 0.50 → stays 30.00")

    # Zero tip, zero bill edge cases.
    r = split(40, 0, 4)
    assert math.isclose(r["tip"], 0.0) and math.isclose(r["per_person"], 10.0)
    r = split(0, 20, 3, round_to=1)
    assert math.isclose(r["total"], 0.0)
    assert math.isclose(r["effective_tip_percent"], 0.0)
    print("zero-tip and zero-bill cases OK")

    # Error cases.
    for bad in [dict(bill=-1, tip_percent=10, people=2),
                dict(bill=10, tip_percent=-5, people=2),
                dict(bill=10, tip_percent=10, people=0)]:
        try:
            split(**bad)
        except ValueError as e:
            print(f"split({bad}) → {e}")

    print("all checks passed")
