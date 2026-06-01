"""Speed / distance / time calculator — pure-Python logic.

The three quantities are tied by the constant-speed relations:
    distance = speed * time
    speed    = distance / time
    time     = distance / speed

Give any two and the third is determined. Each quantity is converted to an
SI base unit (metre, second, metre/second), the missing one is solved for,
and the answer is reported back in every supported unit of that quantity.

Public helper:
    solve(target, a_val, a_unit, b_val, b_unit) -> dict

`target` is "distance", "speed" or "time". The two knowns are passed as
(value, unit) pairs in any order; the solver picks them apart by which
quantity each unit belongs to.
"""

# Conversion factors to SI base units.
#   distance -> metres
#   speed    -> metres per second
#   time     -> seconds
DISTANCE = {
    "mm": 0.001,
    "cm": 0.01,
    "m": 1.0,
    "km": 1000.0,
    "in": 0.0254,
    "ft": 0.3048,
    "yd": 0.9144,
    "mi": 1609.344,
    "nmi": 1852.0,
}

SPEED = {
    "m/s": 1.0,
    "km/h": 1000.0 / 3600.0,
    "mph": 1609.344 / 3600.0,
    "ft/s": 0.3048,
    "knot": 1852.0 / 3600.0,
}

TIME = {
    "s": 1.0,
    "min": 60.0,
    "h": 3600.0,
    "day": 86400.0,
}

# Which quantity each unit family belongs to.
QUANTITY = {
    "distance": DISTANCE,
    "speed": SPEED,
    "time": TIME,
}

# Pretty labels for output.
LABELS = {
    "mm": "mm", "cm": "cm", "m": "m", "km": "km", "in": "in", "ft": "ft",
    "yd": "yd", "mi": "mi", "nmi": "nmi",
    "m/s": "m/s", "km/h": "km/h", "mph": "mph", "ft/s": "ft/s", "knot": "knots",
    "s": "s", "min": "min", "h": "h", "day": "days",
}


def _quantity_of(unit):
    for name, table in QUANTITY.items():
        if unit in table:
            return name
    raise ValueError(f"unknown unit: {unit!r}")


def _to_base(value, unit):
    quantity = _quantity_of(unit)
    return value * QUANTITY[quantity][unit]


def _breakdown(quantity, base_value):
    """Express an SI-base value in every unit of its quantity."""
    table = QUANTITY[quantity]
    rows = []
    for unit, factor in table.items():
        rows.append({"unit": unit, "label": LABELS[unit], "value": base_value / factor})
    return rows


def solve(target, a_val, a_unit, b_val, b_unit):
    if target not in QUANTITY:
        raise ValueError(f"target must be distance, speed or time, got {target!r}")

    knowns = {}
    for value, unit in ((a_val, a_unit), (b_val, b_unit)):
        quantity = _quantity_of(unit)
        if quantity == target:
            raise ValueError(f"both knowns must differ from the target ({target})")
        if quantity in knowns:
            raise ValueError(f"two values given for the same quantity ({quantity})")
        knowns[quantity] = _to_base(value, unit)

    if len(knowns) != 2:
        raise ValueError("need exactly two different quantities to solve the third")

    if target == "distance":
        if "speed" not in knowns or "time" not in knowns:
            raise ValueError("distance needs a speed and a time")
        if knowns["time"] < 0:
            raise ValueError("time must not be negative")
        base = knowns["speed"] * knowns["time"]
    elif target == "speed":
        if "distance" not in knowns or "time" not in knowns:
            raise ValueError("speed needs a distance and a time")
        if knowns["time"] <= 0:
            raise ValueError("time must be positive to find speed")
        base = knowns["distance"] / knowns["time"]
    else:  # time
        if "distance" not in knowns or "speed" not in knowns:
            raise ValueError("time needs a distance and a speed")
        if knowns["speed"] <= 0:
            raise ValueError("speed must be positive to find time")
        base = knowns["distance"] / knowns["speed"]

    return {
        "target": target,
        "base": base,
        "breakdown": _breakdown(target, base),
    }


if __name__ == "__main__":
    # 60 km/h for 2 h -> 120 km.
    r = solve("distance", 60, "km/h", 2, "h")
    dist_km = next(x["value"] for x in r["breakdown"] if x["unit"] == "km")
    print(f"distance: {dist_km:.3f} km (base {r['base']:.1f} m)")
    assert abs(dist_km - 120) < 1e-9

    # 120 km in 2 h -> 60 km/h.
    r = solve("speed", 120, "km", 2, "h")
    kmh = next(x["value"] for x in r["breakdown"] if x["unit"] == "km/h")
    print(f"speed: {kmh:.3f} km/h")
    assert abs(kmh - 60) < 1e-9

    # 100 m at 10 m/s -> 10 s.
    r = solve("time", 100, "m", 10, "m/s")
    secs = next(x["value"] for x in r["breakdown"] if x["unit"] == "s")
    print(f"time: {secs:.3f} s")
    assert abs(secs - 10) < 1e-9

    # Mixed imperial: 60 mph for 30 min -> 30 mi.
    r = solve("distance", 60, "mph", 30, "min")
    miles = next(x["value"] for x in r["breakdown"] if x["unit"] == "mi")
    print(f"distance: {miles:.4f} mi")
    assert abs(miles - 30) < 1e-6

    # Order independence: pass time first.
    r = solve("speed", 2, "h", 120, "km")
    kmh = next(x["value"] for x in r["breakdown"] if x["unit"] == "km/h")
    assert abs(kmh - 60) < 1e-9

    # Argument validation.
    for bad in (
        lambda: solve("speed", 1, "km", 0, "h"),       # divide by zero time
        lambda: solve("time", 1, "km", 0, "km/h"),     # divide by zero speed
        lambda: solve("distance", 1, "km", 2, "mi"),   # same quantity twice
        lambda: solve("distance", 1, "km", 2, "h"),    # known equals target
        lambda: solve("mass", 1, "km", 2, "h"),        # bad target
    ):
        try:
            bad()
        except ValueError as e:
            print(f"rejected: {e}")
        else:
            raise AssertionError("expected ValueError")

    print("all checks passed")
