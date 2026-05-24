"""BMI — pure-Python logic.

    BMI = weight (kg) / height (m)^2

WHO classification:
    < 18.5         Underweight
    18.5 – 24.9    Normal
    25.0 – 29.9    Overweight
    30.0 – 34.9    Obese (Class I)
    35.0 – 39.9    Obese (Class II)
    >= 40.0        Obese (Class III)
"""

LB_PER_KG = 2.2046226218
IN_PER_CM = 0.3937007874


def _category(value):
    if value < 18.5:
        return "Underweight"
    if value < 25:
        return "Normal"
    if value < 30:
        return "Overweight"
    if value < 35:
        return "Obese (Class I)"
    if value < 40:
        return "Obese (Class II)"
    return "Obese (Class III)"


def bmi(weight_kg, height_cm):
    """Compute BMI and the healthy weight range from metric inputs."""
    if weight_kg <= 0 or height_cm <= 0:
        raise ValueError("weight and height must be positive")

    height_m = height_cm / 100
    value = weight_kg / (height_m ** 2)

    return {
        "bmi": round(value, 1),
        "category": _category(value),
        "healthy_min_kg": round(18.5 * height_m ** 2, 1),
        "healthy_max_kg": round(24.9 * height_m ** 2, 1),
    }


def bmi_imperial(weight_lb, height_in):
    """Compute BMI from imperial inputs (pounds, total inches)."""
    weight_kg = weight_lb / LB_PER_KG
    height_cm = height_in / IN_PER_CM
    result = bmi(weight_kg, height_cm)
    result["healthy_min_lb"] = round(result["healthy_min_kg"] * LB_PER_KG, 1)
    result["healthy_max_lb"] = round(result["healthy_max_kg"] * LB_PER_KG, 1)
    return result


if __name__ == "__main__":
    print("Metric: 70 kg, 175 cm")
    r = bmi(70, 175)
    print(f"  BMI {r['bmi']}  ({r['category']})")
    print(f"  Healthy range: {r['healthy_min_kg']}–{r['healthy_max_kg']} kg")
    print()
    print("Imperial: 154 lb, 5 ft 9 in")
    r = bmi_imperial(154, 5 * 12 + 9)
    print(f"  BMI {r['bmi']}  ({r['category']})")
    print(f"  Healthy range: {r['healthy_min_lb']}–{r['healthy_max_lb']} lb")
