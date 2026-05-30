"""Unit converter — length, mass, volume.

Every unit is defined by a single factor: how many base units one of it equals.
The base unit per category is metric (metre, kilogram, litre). To convert a
value from unit A to unit B in the same category:

    value_in_base = value * factor[A]
    result        = value_in_base / factor[B]

That's it — no per-pair conversion tables, just one factor per unit. Factors
use the international (exact) definitions where they exist:
  - 1 inch  = 0.0254 m exactly
  - 1 pound = 0.45359237 kg exactly
  - US fluid measures are based on the US gallon = 3.785411784 L exactly
  - Imperial fluid measures are based on the imperial gallon = 4.54609 L exactly
"""

# category -> { unit_key: (label, factor_to_base) }
# factor_to_base = how many base units one of this unit equals.
UNITS = {
    "length": {  # base: metre
        "mm": ("Millimetre (mm)", 0.001),
        "cm": ("Centimetre (cm)", 0.01),
        "m": ("Metre (m)", 1.0),
        "km": ("Kilometre (km)", 1000.0),
        "in": ("Inch (in)", 0.0254),
        "ft": ("Foot (ft)", 0.3048),
        "yd": ("Yard (yd)", 0.9144),
        "mi": ("Mile (mi)", 1609.344),
        "nmi": ("Nautical mile (nmi)", 1852.0),
    },
    "mass": {  # base: kilogram
        "mg": ("Milligram (mg)", 1e-6),
        "g": ("Gram (g)", 0.001),
        "kg": ("Kilogram (kg)", 1.0),
        "t": ("Metric tonne (t)", 1000.0),
        "oz": ("Ounce (oz)", 0.028349523125),
        "lb": ("Pound (lb)", 0.45359237),
        "st": ("Stone (st)", 6.35029318),
        "ton_us": ("US ton (short)", 907.18474),
        "ton_uk": ("UK ton (long)", 1016.0469088),
    },
    "volume": {  # base: litre
        "ml": ("Millilitre (mL)", 0.001),
        "l": ("Litre (L)", 1.0),
        "m3": ("Cubic metre (m³)", 1000.0),
        "tsp": ("Teaspoon (US)", 0.00492892159375),
        "tbsp": ("Tablespoon (US)", 0.01478676478125),
        "floz": ("Fluid ounce (US)", 0.0295735295625),
        "cup": ("Cup (US)", 0.2365882365),
        "pt": ("Pint (US)", 0.473176473),
        "qt": ("Quart (US)", 0.946352946),
        "gal": ("Gallon (US)", 3.785411784),
        "gal_uk": ("Gallon (imperial)", 4.54609),
    },
}


def convert(value, category, from_unit, to_unit):
    """Convert ``value`` from ``from_unit`` to ``to_unit`` within ``category``.

    Returns a dict with the converted value, the per-unit factor (how many
    ``to_unit`` equal one ``from_unit``), and its inverse.
    """
    value = float(value)
    if category not in UNITS:
        raise ValueError(f"unknown category: {category!r}")
    table = UNITS[category]
    if from_unit not in table:
        raise ValueError(f"unknown {category} unit: {from_unit!r}")
    if to_unit not in table:
        raise ValueError(f"unknown {category} unit: {to_unit!r}")

    from_factor = table[from_unit][1]
    to_factor = table[to_unit][1]

    converted = value * from_factor / to_factor
    factor = from_factor / to_factor  # one from_unit = `factor` to_units

    return {
        "value": value,
        "category": category,
        "from": from_unit,
        "to": to_unit,
        "from_label": table[from_unit][0],
        "to_label": table[to_unit][0],
        "converted": converted,
        "factor": factor,
        "inverse_factor": 1.0 / factor if factor else float("inf"),
    }


if __name__ == "__main__":
    checks = [
        # (value, category, from, to, expected)
        (1, "length", "mi", "km", 1.609344),
        (100, "length", "cm", "m", 1.0),
        (12, "length", "in", "ft", 1.0),
        (1, "length", "m", "in", 39.37007874015748),
        (1, "mass", "kg", "lb", 2.2046226218487757),
        (16, "mass", "oz", "lb", 1.0),
        (1, "mass", "t", "kg", 1000.0),
        (1, "mass", "st", "lb", 14.0),
        (1, "volume", "gal", "l", 3.785411784),
        (1, "volume", "l", "ml", 1000.0),
        (1, "volume", "m3", "l", 1000.0),
        (2, "volume", "cup", "floz", 16.0),
    ]
    ok = True
    for value, cat, f, t, expected in checks:
        got = convert(value, cat, f, t)["converted"]
        good = abs(got - expected) < 1e-9
        ok = ok and good
        flag = "ok " if good else "FAIL"
        print(f"[{flag}] {value} {f} -> {t} ({cat}): {got!r} (expected {expected!r})")

    # round-trip: converting there and back returns the original
    rt = convert(convert(5, "mass", "lb", "kg")["converted"], "mass", "kg", "lb")["converted"]
    print(f"[{'ok ' if abs(rt - 5) < 1e-9 else 'FAIL'}] round-trip 5 lb -> kg -> lb = {rt!r}")

    # error cases
    for bad in (("length", "m", "kg"), ("speed", "m", "m")):
        try:
            convert(1, bad[0], bad[1], bad[2])
            print(f"[FAIL] expected error for {bad}")
        except ValueError as e:
            print(f"[ok ] {bad}: {e}")

    print("ALL OK" if ok else "SOME CHECKS FAILED")
