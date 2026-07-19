"""Daily protein & nutrition targets from body weight — pure-Python logic.

Everything keys off body weight (kg), an activity level, and a goal.

Protein is the headline number. Sports-nutrition consensus (ISSN, ACSM)
expresses protein need as grams per kg of body weight, scaling up with
training volume and up again when eating in a deficit (protein spares
lean mass) or building muscle:

    activity      g/kg (low – high)
    sedentary     0.8 – 1.0     (RDA + a small buffer)
    light         1.0 – 1.4
    moderate      1.2 – 1.6
    active        1.4 – 1.8
    athlete       1.6 – 2.2

Goal shifts that band: a fat-loss deficit nudges it up (protein sparing),
muscle gain raises the floor.

The rest is derived:
    calories  maintenance ≈ weight(kg) × kcal-per-kg factor (activity),
              then ×0.80 to lose fat / ×1.10 to build muscle
    water     ~33 ml/kg (30–40 ml/kg band)
    fat       ~0.9 g/kg (0.6–1.2 g/kg band) — a hormone/absorption floor
    carbs     the remaining calories after protein + fat
    fiber     14 g per 1000 kcal (Dietary Guidelines)

These are population starting points, not a prescription. Real needs vary
with age, sex, body composition, kidney health and medical conditions.
"""

LB_PER_KG = 2.2046226218
KCAL_PER_G_PROTEIN = 4
KCAL_PER_G_CARB = 4
KCAL_PER_G_FAT = 9
ML_PER_CUP = 240

# activity level -> (protein low g/kg, protein high g/kg, kcal per kg maintenance)
_ACTIVITY = {
    "sedentary": (0.8, 1.0, 28),
    "light": (1.0, 1.4, 31),
    "moderate": (1.2, 1.6, 34),
    "active": (1.4, 1.8, 38),
    "athlete": (1.6, 2.2, 43),
}

# goal -> (protein g/kg shift, calorie multiplier vs maintenance)
_GOAL = {
    "maintain": (0.0, 1.00),
    "lose_fat": (0.3, 0.80),
    "build_muscle": (0.2, 1.10),
}

_PROTEIN_CEILING = 2.4  # g/kg — above this there's little added benefit


def to_kg(weight, unit):
    """Normalize a weight in kg or lb to kilograms."""
    if weight <= 0:
        raise ValueError("weight must be positive")
    return weight / LB_PER_KG if unit == "lb" else float(weight)


def protein_target(weight_kg, activity, goal):
    """Protein band (g and g/kg) and a recommended midpoint."""
    low_kg, high_kg, _ = _ACTIVITY[activity]
    shift, _ = _GOAL[goal]
    low_kg = min(low_kg + shift, _PROTEIN_CEILING)
    high_kg = min(high_kg + shift, _PROTEIN_CEILING)
    if goal == "build_muscle":            # raise the floor for hypertrophy
        low_kg = max(low_kg, 1.6)
    rec_kg = (low_kg + high_kg) / 2
    return {
        "low_per_kg": round(low_kg, 2),
        "high_per_kg": round(high_kg, 2),
        "rec_per_kg": round(rec_kg, 2),
        "low_g": round(low_kg * weight_kg),
        "high_g": round(high_kg * weight_kg),
        "rec_g": round(rec_kg * weight_kg),
    }


def calorie_target(weight_kg, activity, goal):
    """Rough maintenance calories and the goal-adjusted daily target."""
    _, _, kcal_per_kg = _ACTIVITY[activity]
    _, mult = _GOAL[goal]
    maintenance = weight_kg * kcal_per_kg
    return {
        "maintenance": round(maintenance / 10) * 10,
        "target": round(maintenance * mult / 10) * 10,
    }


def water_target(weight_kg):
    """Daily fluid target — ~33 ml/kg with a 30–40 ml/kg band."""
    rec_ml = 33 * weight_kg
    return {
        "low_ml": round(30 * weight_kg / 10) * 10,
        "high_ml": round(40 * weight_kg / 10) * 10,
        "rec_ml": round(rec_ml / 10) * 10,
        "rec_l": round(rec_ml / 1000, 1),
        "cups": round(rec_ml / ML_PER_CUP),
    }


def fat_target(weight_kg, target_calories):
    """Fat floor/band (~0.9 g/kg) and its share of the calorie target."""
    rec_g = 0.9 * weight_kg
    pct = 100 * rec_g * KCAL_PER_G_FAT / target_calories if target_calories else 0
    return {
        "low_g": round(0.6 * weight_kg),
        "high_g": round(1.2 * weight_kg),
        "rec_g": round(rec_g),
        "pct_of_target": round(pct),
    }


def plan(weight, unit="kg", activity="moderate", goal="maintain", meals=3):
    """Assemble the full daily nutrition plan from body weight."""
    if activity not in _ACTIVITY:
        raise ValueError("unknown activity level: %r" % activity)
    if goal not in _GOAL:
        raise ValueError("unknown goal: %r" % goal)
    if meals < 1:
        raise ValueError("meals must be at least 1")

    weight_kg = to_kg(weight, unit)
    protein = protein_target(weight_kg, activity, goal)
    calories = calorie_target(weight_kg, activity, goal)
    fat = fat_target(weight_kg, calories["target"])

    # carbs take whatever calories remain after protein + fat
    used = protein["rec_g"] * KCAL_PER_G_PROTEIN + fat["rec_g"] * KCAL_PER_G_FAT
    carb_kcal = max(calories["target"] - used, 0)
    carb_g = round(carb_kcal / KCAL_PER_G_CARB)

    fiber_g = round(14 * calories["target"] / 1000)

    protein["per_meal_g"] = round(protein["rec_g"] / meals)

    return {
        "weight_kg": round(weight_kg, 1),
        "meals": meals,
        "protein": protein,
        "calories": calories,
        "water": water_target(weight_kg),
        "fat": fat,
        "carbs": {"rec_g": carb_g, "per_kg": round(carb_g / weight_kg, 1)},
        "fiber": {"rec_g": fiber_g},
    }


if __name__ == "__main__":
    print("70 kg · moderately active · maintain · 3 meals")
    p = plan(70, "kg", "moderate", "maintain", 3)
    pr = p["protein"]
    print(f"  Protein   {pr['rec_g']} g/day  "
          f"({pr['low_g']}–{pr['high_g']} g, {pr['rec_per_kg']} g/kg) "
          f"≈ {pr['per_meal_g']} g/meal")
    print(f"  Calories  {p['calories']['target']} kcal "
          f"(maintenance {p['calories']['maintenance']})")
    print(f"  Water     {p['water']['rec_l']} L  (~{p['water']['cups']} cups)")
    print(f"  Fat       {p['fat']['rec_g']} g  ({p['fat']['pct_of_target']}% of kcal)")
    print(f"  Carbs     {p['carbs']['rec_g']} g  ({p['carbs']['per_kg']} g/kg)")
    print(f"  Fiber     {p['fiber']['rec_g']} g")

    # sanity checks
    assert pr["rec_g"] == round(pr["rec_per_kg"] * 70)
    # deficit for fat loss raises protein g/kg and drops calories
    lean = plan(70, "kg", "moderate", "lose_fat")
    assert lean["protein"]["rec_per_kg"] > pr["rec_per_kg"]
    assert lean["calories"]["target"] < p["calories"]["target"]
    # muscle gain floors protein at >=1.6 g/kg and adds calories
    bulk = plan(70, "kg", "moderate", "build_muscle")
    assert bulk["protein"]["low_per_kg"] >= 1.6
    assert bulk["calories"]["target"] > p["calories"]["target"]
    # protein g/kg never exceeds the ceiling
    assert plan(90, "kg", "athlete", "lose_fat")["protein"]["high_per_kg"] <= 2.4
    # lb input matches the kg equivalent
    assert plan(154, "lb", "light", "maintain")["weight_kg"] == 69.9
    # carbs never go negative even at a steep deficit for a light eater
    assert plan(50, "kg", "sedentary", "lose_fat")["carbs"]["rec_g"] >= 0
    print("\nAll sanity checks passed.")
