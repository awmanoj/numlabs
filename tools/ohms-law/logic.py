"""Ohm's Law calculator — pure-Python logic.

Four quantities are tied together by Ohm's law and the power relation:

    V = I * R          (voltage = current * resistance)
    P = V * I          (power   = voltage * current)

and the two derived forms P = I**2 * R = V**2 / R. Together these let you
recover all four quantities from any *two* of them — the classic "Ohm's law
wheel". There are six possible pairs of knowns; each one determines the other
two unambiguously.

Public helper:
    solve(q1, v1, u1, q2, v2, u2) -> dict

Each known is a (quantity, value, unit) triple. `quantity` is one of
"voltage", "current", "resistance", "power"; `value` is non-negative; `unit`
is one of the prefixed units below and must belong to that quantity. Order
does not matter. Every quantity is converted to its SI base unit (volt,
ampere, ohm, watt), the two unknowns are solved for, and every quantity is
reported back in all of its supported units.
"""

# Conversion factors to SI base units (volt, ampere, ohm, watt).
# Unit keys are ASCII-safe; pretty symbols live in LABELS.
VOLTAGE = {
    "uV": 1e-6,
    "mV": 1e-3,
    "V": 1.0,
    "kV": 1e3,
    "MV": 1e6,
}

CURRENT = {
    "uA": 1e-6,
    "mA": 1e-3,
    "A": 1.0,
    "kA": 1e3,
}

RESISTANCE = {
    "mohm": 1e-3,
    "ohm": 1.0,
    "kohm": 1e3,
    "Mohm": 1e6,
    "Gohm": 1e9,
}

POWER = {
    "uW": 1e-6,
    "mW": 1e-3,
    "W": 1.0,
    "kW": 1e3,
    "MW": 1e6,
}

QUANTITY = {
    "voltage": VOLTAGE,
    "current": CURRENT,
    "resistance": RESISTANCE,
    "power": POWER,
}

# Fixed display order for the four quantities.
ORDER = ["voltage", "current", "resistance", "power"]

# Human names for each quantity.
NAMES = {
    "voltage": "Voltage",
    "current": "Current",
    "resistance": "Resistance",
    "power": "Power",
}

# Pretty labels for output units.
LABELS = {
    "uV": "µV", "mV": "mV", "V": "V", "kV": "kV", "MV": "MV",
    "uA": "µA", "mA": "mA", "A": "A", "kA": "kA",
    "mohm": "mΩ", "ohm": "Ω", "kohm": "kΩ", "Mohm": "MΩ", "Gohm": "GΩ",
    "uW": "µW", "mW": "mW", "W": "W", "kW": "kW", "MW": "MW",
}


def _quantity_of(unit):
    for name, table in QUANTITY.items():
        if unit in table:
            return name
    raise ValueError(f"unknown unit: {unit!r}")


def _to_base(value, unit):
    return value * QUANTITY[_quantity_of(unit)][unit]


def _breakdown(quantity, base_value):
    """Express an SI-base value in every unit of its quantity."""
    table = QUANTITY[quantity]
    return [
        {"unit": unit, "label": LABELS[unit], "value": base_value / factor}
        for unit, factor in table.items()
    ]


def solve(q1, v1, u1, q2, v2, u2):
    known = {}
    for q, v, u in ((q1, v1, u1), (q2, v2, u2)):
        if q not in QUANTITY:
            raise ValueError(f"unknown quantity: {q!r}")
        if _quantity_of(u) != q:
            raise ValueError(f"unit {u!r} does not belong to {q}")
        if q in known:
            raise ValueError(f"two values given for {q}")
        if v < 0:
            raise ValueError(f"{NAMES[q].lower()} must not be negative")
        known[q] = _to_base(v, u)

    if len(known) != 2:
        raise ValueError("need exactly two different quantities")

    keys = frozenset(known)
    V = known.get("voltage")
    I = known.get("current")
    R = known.get("resistance")
    P = known.get("power")
    formulas = []

    if keys == {"voltage", "current"}:
        if I == 0:
            raise ValueError("current must be positive to find resistance")
        R = V / I
        P = V * I
        formulas = ["R = V ÷ I", "P = V × I"]
    elif keys == {"voltage", "resistance"}:
        if R <= 0:
            raise ValueError("resistance must be positive")
        I = V / R
        P = V * V / R
        formulas = ["I = V ÷ R", "P = V² ÷ R"]
    elif keys == {"voltage", "power"}:
        if V <= 0:
            raise ValueError("voltage must be positive to find current")
        if P <= 0:
            raise ValueError("power must be positive to find resistance")
        I = P / V
        R = V * V / P
        formulas = ["I = P ÷ V", "R = V² ÷ P"]
    elif keys == {"current", "resistance"}:
        V = I * R
        P = I * I * R
        formulas = ["V = I × R", "P = I² × R"]
    elif keys == {"current", "power"}:
        if I == 0:
            raise ValueError("current must be positive to find voltage")
        V = P / I
        R = P / (I * I)
        formulas = ["V = P ÷ I", "R = P ÷ I²"]
    else:  # {"resistance", "power"}
        if R <= 0:
            raise ValueError("resistance must be positive")
        I = (P / R) ** 0.5
        V = (P * R) ** 0.5
        formulas = ["I = √(P ÷ R)", "V = √(P × R)"]

    base = {"voltage": V, "current": I, "resistance": R, "power": P}
    solved = [q for q in ORDER if q not in known]

    quantities = []
    for q in ORDER:
        quantities.append({
            "key": q,
            "name": NAMES[q],
            "given": q in known,
            "base": base[q],
            "breakdown": _breakdown(q, base[q]),
        })

    return {
        "quantities": quantities,
        "solved": solved,
        "formulas": formulas,
    }


if __name__ == "__main__":
    def get(res, key):
        return next(q["base"] for q in res["quantities"] if q["key"] == key)

    # Reference circuit: 12 V across 6 ohm -> 2 A, 24 W. Check all six pairs.
    pairs = [
        ("voltage", 12, "V", "current", 2, "A"),
        ("voltage", 12, "V", "resistance", 6, "ohm"),
        ("voltage", 12, "V", "power", 24, "W"),
        ("current", 2, "A", "resistance", 6, "ohm"),
        ("current", 2, "A", "power", 24, "W"),
        ("resistance", 6, "ohm", "power", 24, "W"),
    ]
    for p in pairs:
        r = solve(*p)
        assert abs(get(r, "voltage") - 12) < 1e-9, p
        assert abs(get(r, "current") - 2) < 1e-9, p
        assert abs(get(r, "resistance") - 6) < 1e-9, p
        assert abs(get(r, "power") - 24) < 1e-9, p
    print("all six pairs reproduce 12 V / 2 A / 6 Ω / 24 W")

    # Prefixed units: 1 kV across 1 mA -> 1 Mohm, 1 W.
    r = solve("voltage", 1, "kV", "current", 1, "mA")
    assert abs(get(r, "resistance") - 1e6) < 1e-3
    assert abs(get(r, "power") - 1.0) < 1e-9
    r_row = next(q for q in r["quantities"] if q["key"] == "resistance")
    mohm = next(x["value"] for x in r_row["breakdown"] if x["unit"] == "Mohm")
    print(f"1 kV / 1 mA -> {mohm:.4f} MΩ, 1 W")
    assert abs(mohm - 1.0) < 1e-9

    # Order independence.
    a = solve("current", 2, "A", "voltage", 12, "V")
    b = solve("voltage", 12, "V", "current", 2, "A")
    assert abs(get(a, "power") - get(b, "power")) < 1e-12

    # Argument validation.
    for bad in (
        lambda: solve("voltage", 12, "V", "current", 0, "A"),    # R = V/0
        lambda: solve("voltage", 12, "V", "resistance", 0, "ohm"),  # I = V/0
        lambda: solve("resistance", 0, "ohm", "power", 4, "W"),  # sqrt(P/0)
        lambda: solve("voltage", 12, "V", "voltage", 5, "V"),    # same quantity
        lambda: solve("voltage", -1, "V", "current", 2, "A"),    # negative input
        lambda: solve("voltage", 12, "mA", "current", 2, "A"),   # unit/qty mismatch
        lambda: solve("mass", 1, "V", "current", 2, "A"),        # bad quantity
    ):
        try:
            bad()
        except ValueError as e:
            print(f"rejected: {e}")
        else:
            raise AssertionError("expected ValueError")

    print("all checks passed")
