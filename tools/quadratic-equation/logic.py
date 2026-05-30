"""Quadratic equation solver — ax² + bx + c = 0.

Solves via the quadratic formula x = (−b ± √(b² − 4ac)) / 2a, classifying the
roots from the sign of the discriminant Δ = b² − 4ac:

  Δ > 0  → two distinct real roots
  Δ = 0  → one repeated real root
  Δ < 0  → two complex-conjugate roots

Also reports the parabola's vertex, axis of symmetry, the sum/product of the
roots (Vieta's formulas), and a factored form when the roots are rational.

`a` must be non-zero; with a = 0 the equation is linear, which we report as
such rather than dividing by zero.
"""

import cmath
import math
from fractions import Fraction

EPS = 1e-12


def _fmt_complex(z):
    """Real numbers come back as floats; genuinely complex ones as a
    (re, im) pair so the front end can render `re ± im·i`."""
    if abs(z.imag) < EPS:
        return {"kind": "real", "value": z.real}
    return {"kind": "complex", "re": z.real, "im": z.imag}


def _is_int(x):
    return abs(x - round(x)) < 1e-9


def _factored_form(a, b, c):
    """Return a string like `(2x − 3)(x + 1)` when a, b, c are integers and
    the roots are rational, else None. Built from the exact rational roots so
    no floating-point round-off leaks into the display."""
    if not (_is_int(a) and _is_int(b) and _is_int(c)):
        return None
    a, b, c = int(round(a)), int(round(b)), int(round(c))
    disc = b * b - 4 * a * c
    if disc < 0:
        return None
    root = math.isqrt(disc)
    if root * root != disc:
        return None  # irrational roots — leave it unfactored

    # Rational roots r1, r2 = (−b ± √disc) / 2a, reduced to lowest terms.
    # Sort ascending so the factored form is stable regardless of a's sign.
    r1, r2 = sorted([Fraction(-b + root, 2 * a), Fraction(-b - root, 2 * a)])

    def factor_for(r):
        # x = p/q  ⇒  (q·x − p), with q > 0. Clearing the denominator pulls a
        # factor of q out front, so the caller divides `a` by each q.
        q, p = r.denominator, r.numerator
        xs = "x" if q == 1 else f"{q}x"
        if p == 0:
            return q, xs
        sign = "−" if p > 0 else "+"
        return q, f"({xs} {sign} {abs(p)})"

    q1, f1 = factor_for(r1)
    q2, f2 = factor_for(r2)
    # a·(x−r1)(x−r2) = (a / q1q2)·f1·f2 — the leading factor left over after
    # the denominators are cleared into the factors themselves.
    lead_coeff = Fraction(int(round(a)), q1 * q2)
    lead = "" if lead_coeff == 1 else ("−" if lead_coeff == -1 else str(lead_coeff))
    body = f"{f1}{f2}" if r1 != r2 else f"{f1}²"
    return f"{lead}{body}"


def solve(a, b, c):
    if a is None or b is None or c is None:
        raise ValueError("Enter values for a, b and c")
    a, b, c = float(a), float(b), float(c)

    if abs(a) < EPS:
        # Degenerate: bx + c = 0.
        if abs(b) < EPS:
            if abs(c) < EPS:
                raise ValueError("0 = 0 is an identity, not an equation")
            raise ValueError("No solution: this reduces to a non-zero constant")
        return {
            "degenerate": True,
            "nature": "linear (a = 0)",
            "roots": [_fmt_complex(complex(-c / b, 0.0))],
            "discriminant": None,
        }

    disc = b * b - 4 * a * c

    if disc > EPS:
        nature = "two distinct real roots"
        s = math.sqrt(disc)
        roots = [(-b + s) / (2 * a), (-b - s) / (2 * a)]
        roots = [_fmt_complex(complex(r, 0.0)) for r in roots]
    elif disc < -EPS:
        nature = "two complex-conjugate roots"
        s = cmath.sqrt(disc)
        roots = [(-b + s) / (2 * a), (-b - s) / (2 * a)]
        roots = [_fmt_complex(r) for r in roots]
    else:
        nature = "one repeated real root"
        r = -b / (2 * a)
        roots = [_fmt_complex(complex(r, 0.0))]

    return {
        "degenerate": False,
        "discriminant": disc,
        "nature": nature,
        "roots": roots,
        "vertex_x": -b / (2 * a),
        "vertex_y": c - b * b / (4 * a),
        "axis": -b / (2 * a),
        "sum_roots": -b / a,       # Vieta: x1 + x2 = −b/a
        "product_roots": c / a,    # Vieta: x1·x2 = c/a
        "factored": _factored_form(a, b, c),
    }


if __name__ == "__main__":
    # Two distinct real roots: x² − 5x + 6 = (x−2)(x−3)
    r = solve(1, -5, 6)
    vals = sorted(x["value"] for x in r["roots"])
    assert vals == [2.0, 3.0], r
    assert r["nature"] == "two distinct real roots"
    assert r["factored"] == "(x − 2)(x − 3)", r["factored"]
    print(f"x²−5x+6 → roots {vals}, factored {r['factored']}")

    # Repeated root: x² − 4x + 4 = (x−2)²
    r = solve(1, -4, 4)
    assert len(r["roots"]) == 1 and math.isclose(r["roots"][0]["value"], 2.0)
    assert r["factored"] == "(x − 2)²", r["factored"]
    print(f"x²−4x+4 → repeated root, factored {r['factored']}")

    # Complex roots: x² + x + 1 = 0
    r = solve(1, 1, 1)
    assert r["roots"][0]["kind"] == "complex"
    assert math.isclose(r["roots"][0]["re"], -0.5)
    assert math.isclose(abs(r["roots"][0]["im"]), math.sqrt(3) / 2)
    print(f"x²+x+1 → complex {r['roots'][0]['re']:.4f} ± "
          f"{abs(r['roots'][0]['im']):.4f}i")

    # Leading coefficient ≠ 1: 2x² − 3x − 2 = (2x + 1)(x − 2)
    r = solve(2, -3, -2)
    vals = sorted(x["value"] for x in r["roots"])
    assert vals == [-0.5, 2.0], r
    assert r["factored"] == "(2x + 1)(x − 2)", r["factored"]
    print(f"2x²−3x−2 → roots {vals}, factored {r['factored']}")

    # Vieta + vertex on 2x² − 3x − 2
    assert math.isclose(r["sum_roots"], 1.5)
    assert math.isclose(r["product_roots"], -1.0)
    assert math.isclose(r["vertex_x"], 0.75)
    assert math.isclose(r["vertex_y"], -3.125)
    print(f"   sum {r['sum_roots']}, product {r['product_roots']}, "
          f"vertex ({r['vertex_x']}, {r['vertex_y']})")

    # Irrational roots stay unfactored: x² − 2 = 0
    r = solve(1, 0, -2)
    assert r["factored"] is None
    vals = sorted(x["value"] for x in r["roots"])
    assert math.isclose(vals[1], math.sqrt(2))
    print(f"x²−2 → roots ±√2 ≈ {vals[1]:.4f}, factored {r['factored']}")

    # Linear degenerate: 0x² + 2x − 4 = 0 → x = 2
    r = solve(0, 2, -4)
    assert r["degenerate"] and math.isclose(r["roots"][0]["value"], 2.0)
    print(f"2x−4 → linear, x = {r['roots'][0]['value']}")

    # Error cases
    for bad in [(0, 0, 5), (0, 0, 0)]:
        try:
            solve(*bad)
        except ValueError as e:
            print(f"solve{bad} → {e}")

    print("all checks passed")
