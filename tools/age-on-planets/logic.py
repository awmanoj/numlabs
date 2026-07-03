"""Age on other planets — pure-Python logic.

Your age is really "how many times has Earth gone round the Sun since you were
born". Swap Earth's orbit for another planet's and you get your age there. This
module turns a birthdate + a reference date into your age on every planet, plus
the date of your next birthday on each.

The browser passes both dates in as ISO strings so the math is a pure function
of its inputs (no hidden `date.today()`), which keeps it testable in CPython and
identical under Pyodide. Runs standalone: `python3 logic.py`.
"""

from datetime import date, timedelta
import math

# Sidereal orbital periods in Earth days (how long one lap round the Sun takes).
# Same reference frame for every body, Earth included, so ratios stay honest.
PLANETS = [
    {"name": "Mercury", "period_days": 87.969,   "dwarf": False,
     "note": "closest to the Sun — a year flies by"},
    {"name": "Venus",   "period_days": 224.701,  "dwarf": False,
     "note": "Earth's hotter twin"},
    {"name": "Earth",   "period_days": 365.256,  "dwarf": False,
     "note": "home — your usual age"},
    {"name": "Mars",    "period_days": 686.980,  "dwarf": False,
     "note": "the red planet"},
    {"name": "Jupiter", "period_days": 4332.589, "dwarf": False,
     "note": "the giant — long, slow years"},
    {"name": "Saturn",  "period_days": 10759.22, "dwarf": False,
     "note": "the ringed one"},
    {"name": "Uranus",  "period_days": 30688.5,  "dwarf": False,
     "note": "tipped on its side"},
    {"name": "Neptune", "period_days": 60182.0,  "dwarf": False,
     "note": "farthest planet — barely one lap in a lifetime"},
    {"name": "Pluto",   "period_days": 90560.0,  "dwarf": True,
     "note": "dwarf planet, but too fun to leave out"},
]


def _parse(iso):
    """Parse 'YYYY-MM-DD' (ignores any time part) into a date."""
    y, m, d = (int(x) for x in iso.strip().split("T")[0].split("-"))
    return date(y, m, d)


def earth_days_lived(birth_iso, now_iso):
    """Whole Earth days between birthdate and the reference date."""
    birth = _parse(birth_iso)
    now = _parse(now_iso)
    if birth > now:
        raise ValueError("Birthdate cannot be in the future")
    return (now - birth).days


def planet_age(period_days, days_lived):
    """Age in a planet's years = Earth days lived / that planet's year length."""
    return days_lived / period_days


def next_birthday(period_days, days_lived, now_iso):
    """When the next whole planet-year ticks over.

    Returns (iso_date, days_from_now). The next birthday is the smallest whole
    number of planet-years strictly greater than the current age.
    """
    current = planet_age(period_days, days_lived)
    next_age = math.floor(current) + 1
    target_earth_days = next_age * period_days
    days_from_now = math.ceil(target_earth_days - days_lived)
    when = _parse(now_iso) + timedelta(days=days_from_now)
    return when.isoformat(), days_from_now, next_age


def ages(birth_iso, now_iso):
    """Full per-planet table: age, year length, and next birthday everywhere."""
    days = earth_days_lived(birth_iso, now_iso)
    rows = []
    for p in PLANETS:
        iso, days_from_now, next_age = next_birthday(
            p["period_days"], days, now_iso)
        rows.append({
            "name": p["name"],
            "dwarf": p["dwarf"],
            "note": p["note"],
            "period_earth_years": round(p["period_days"] / 365.256, 3),
            "age_years": round(planet_age(p["period_days"], days), 2),
            "next_birthday": iso,
            "days_to_next": days_from_now,
            "next_age": next_age,
        })
    return {"earth_days": days, "planets": rows}


if __name__ == "__main__":
    # Reference case from the tool's preview: born 1990-06-15, "today" 2026-07-02.
    result = ages("1990-06-15", "2026-07-02")
    days = result["earth_days"]
    assert days == (date(2026, 7, 2) - date(1990, 6, 15)).days

    by_name = {r["name"]: r for r in result["planets"]}
    # Earth age should match the ordinary "years since birth" (36 in 2026).
    assert 36.0 <= by_name["Earth"]["age_years"] < 36.2, by_name["Earth"]
    # Mercury's year is ~4.15x shorter, so its age is ~4.15x Earth's.
    assert by_name["Mercury"]["age_years"] > by_name["Earth"]["age_years"] * 4
    # Neptune: barely a lap and a half in a lifetime.
    assert by_name["Neptune"]["age_years"] < 1, by_name["Neptune"]
    # Next birthday must be in the future and count toward next_age.
    for r in result["planets"]:
        assert r["days_to_next"] > 0, r
        assert r["next_age"] == int(r["age_years"]) + 1 or \
            r["next_age"] == math.floor(r["age_years"]) + 1

    print(f"Born 1990-06-15 — {days:,} Earth days old\n")
    print(f"{'Planet':<9}{'Age (its years)':>16}{'Year =':>12}{'Next b-day':>14}")
    for r in result["planets"]:
        tag = " (dwarf)" if r["dwarf"] else ""
        print(f"{r['name']:<9}{r['age_years']:>16}"
              f"{str(r['period_earth_years']) + ' yr':>12}"
              f"{r['next_birthday']:>14}{tag}")
