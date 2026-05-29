"""Triangle solver — sides, angles, area.

Five classical configurations:
  SSS  — three sides
  SAS  — two sides + the included angle
  ASA  — two angles + the included side
  AAS  — two angles + a non-included side
  SSA  — two sides + a non-included angle (the ambiguous case: 0, 1, or 2
         triangles)

Convention: side `a` is opposite angle `A`, side `b` opposite `B`,
side `c` opposite `C`. Angles are in degrees on the I/O boundary and in
radians inside `math.acos` / `math.asin` calls.
"""

import math

EPS = 1e-9


def _clamp(x, lo=-1.0, hi=1.0):
    return max(lo, min(hi, x))


def _check_positive(name, x):
    if x is None or x <= 0:
        raise ValueError(f"{name} must be greater than 0")


def _check_angle(name, deg):
    if deg is None or deg <= 0 or deg >= 180:
        raise ValueError(f"{name} must be between 0° and 180° (exclusive)")


def _classify_sides(a, b, c):
    s = sorted([a, b, c])
    if math.isclose(s[0], s[2], rel_tol=1e-9):
        return "equilateral"
    if (math.isclose(s[0], s[1], rel_tol=1e-9)
            or math.isclose(s[1], s[2], rel_tol=1e-9)):
        return "isosceles"
    return "scalene"


def _classify_angles(A, B, C):
    largest = max(A, B, C)
    if math.isclose(largest, 90.0, abs_tol=1e-6):
        return "right"
    if largest > 90.0:
        return "obtuse"
    return "acute"


def _finalize(a, b, c, A, B, C):
    perimeter = a + b + c
    s = perimeter / 2
    # Heron's formula. Clamp the product against tiny negative values from
    # floating-point noise on near-degenerate triangles.
    area = math.sqrt(max(0.0, s * (s - a) * (s - b) * (s - c)))
    return {
        "a": a, "b": b, "c": c,
        "A": A, "B": B, "C": C,
        "perimeter": perimeter,
        "area": area,
        "side_type": _classify_sides(a, b, c),
        "angle_type": _classify_angles(A, B, C),
    }


def solve_sss(a, b, c):
    _check_positive("a", a)
    _check_positive("b", b)
    _check_positive("c", c)
    if a + b <= c + EPS or a + c <= b + EPS or b + c <= a + EPS:
        raise ValueError(
            "Sides do not form a triangle (each side must be less "
            "than the sum of the other two)"
        )
    # Law of cosines for two angles, then 180 − sum for the third (keeps
    # rounding cleaner than running acos a third time).
    A = math.degrees(math.acos(_clamp((b*b + c*c - a*a) / (2*b*c))))
    B = math.degrees(math.acos(_clamp((a*a + c*c - b*b) / (2*a*c))))
    C = 180.0 - A - B
    return [_finalize(a, b, c, A, B, C)]


def solve_sas(b, A, c):
    """Two sides (b, c) and the included angle A between them."""
    _check_positive("b", b)
    _check_positive("c", c)
    _check_angle("A", A)
    A_rad = math.radians(A)
    a = math.sqrt(b*b + c*c - 2*b*c*math.cos(A_rad))
    B = math.degrees(math.acos(_clamp((a*a + c*c - b*b) / (2*a*c))))
    C = 180.0 - A - B
    return [_finalize(a, b, c, A, B, C)]


def solve_asa(A, c, B):
    """Two angles (A, B) and the side c lying between them."""
    _check_angle("A", A)
    _check_angle("B", B)
    _check_positive("c", c)
    if A + B >= 180.0 - EPS:
        raise ValueError("Angles A + B must be less than 180°")
    C = 180.0 - A - B
    sin_C = math.sin(math.radians(C))
    a = c * math.sin(math.radians(A)) / sin_C
    b = c * math.sin(math.radians(B)) / sin_C
    return [_finalize(a, b, c, A, B, C)]


def solve_aas(A, B, a):
    """Two angles and a non-included side: a is opposite A."""
    _check_angle("A", A)
    _check_angle("B", B)
    _check_positive("a", a)
    if A + B >= 180.0 - EPS:
        raise ValueError("Angles A + B must be less than 180°")
    C = 180.0 - A - B
    sin_A = math.sin(math.radians(A))
    b = a * math.sin(math.radians(B)) / sin_A
    c = a * math.sin(math.radians(C)) / sin_A
    return [_finalize(a, b, c, A, B, C)]


def solve_ssa(a, b, A):
    """Two sides and a non-included angle (the ambiguous case).

    `a` is the side opposite the given angle `A`; `b` is the other side.
    Returns 1 or 2 solutions; raises if none exist.
    """
    _check_positive("a", a)
    _check_positive("b", b)
    _check_angle("A", A)
    A_rad = math.radians(A)
    sin_B = b * math.sin(A_rad) / a
    if sin_B > 1.0 + EPS:
        raise ValueError("No triangle exists with these inputs")
    sin_B = _clamp(sin_B)
    B1 = math.degrees(math.asin(sin_B))

    solutions = []
    C1 = 180.0 - A - B1
    if C1 > EPS:
        c1 = a * math.sin(math.radians(C1)) / math.sin(A_rad)
        solutions.append(_finalize(a, b, c1, A, B1, C1))

    # Second branch with obtuse B is only valid when A itself is acute and
    # the supplementary angle leaves room for a positive C.
    if A < 90.0 - EPS:
        B2 = 180.0 - B1
        C2 = 180.0 - A - B2
        if not math.isclose(B2, B1, abs_tol=1e-9) and C2 > EPS:
            c2 = a * math.sin(math.radians(C2)) / math.sin(A_rad)
            solutions.append(_finalize(a, b, c2, A, B2, C2))

    if not solutions:
        raise ValueError("No triangle exists with these inputs")
    return solutions


def solve(mode, **kw):
    if mode == "sss":
        return solve_sss(kw["a"], kw["b"], kw["c"])
    if mode == "sas":
        return solve_sas(kw["b"], kw["A"], kw["c"])
    if mode == "asa":
        return solve_asa(kw["A"], kw["c"], kw["B"])
    if mode == "aas":
        return solve_aas(kw["A"], kw["B"], kw["a"])
    if mode == "ssa":
        return solve_ssa(kw["a"], kw["b"], kw["A"])
    raise ValueError(f"Unknown mode '{mode}'")


if __name__ == "__main__":
    # SSS: 3-4-5 right triangle
    r = solve_sss(3, 4, 5)[0]
    assert math.isclose(r["C"], 90.0, abs_tol=1e-6), r
    assert math.isclose(r["area"], 6.0, abs_tol=1e-6), r
    assert r["angle_type"] == "right" and r["side_type"] == "scalene"
    print(f"SSS 3-4-5  → C={r['C']:.4f}°, area={r['area']:.4f}")

    # SSS: equilateral
    r = solve_sss(7, 7, 7)[0]
    assert math.isclose(r["A"], 60.0, abs_tol=1e-6)
    assert r["side_type"] == "equilateral"
    print(f"SSS 7-7-7  → A={r['A']:.4f}°, area={r['area']:.4f}")

    # SAS: angle between two equal sides of 5 at 60° → equilateral 5
    r = solve_sas(5, 60, 5)[0]
    assert math.isclose(r["a"], 5.0, abs_tol=1e-6)
    print(f"SAS 5,60°,5 → a={r['a']:.4f}, B={r['B']:.4f}°")

    # ASA: symmetric
    r = solve_asa(45, 10, 45)[0]
    assert math.isclose(r["C"], 90.0, abs_tol=1e-6)
    print(f"ASA 45°,10,45° → c-side a={r['a']:.4f}, C={r['C']:.4f}°")

    # AAS
    r = solve_aas(30, 60, 5)[0]
    assert math.isclose(r["C"], 90.0, abs_tol=1e-6)
    print(f"AAS 30°,60°,a=5 → b={r['b']:.4f}, c={r['c']:.4f}")

    # SSA ambiguous: a=6, b=8, A=30° → two triangles
    rs = solve_ssa(6, 8, 30)
    assert len(rs) == 2, len(rs)
    print(f"SSA 6,8,30° → {len(rs)} triangles")
    for s in rs:
        print(f"   B={s['B']:.4f}°  C={s['C']:.4f}°  c={s['c']:.4f}")

    # SSA single (a >= b)
    rs = solve_ssa(10, 6, 40)
    assert len(rs) == 1
    print(f"SSA 10,6,40° → {len(rs)} triangle")

    # SSA no triangle (b·sinA > a)
    try:
        solve_ssa(1, 10, 80)
    except ValueError as e:
        print(f"SSA 1,10,80° → {e}")

    # Triangle inequality
    try:
        solve_sss(1, 2, 5)
    except ValueError as e:
        print(f"SSS 1,2,5 → {e}")

    # Bad inputs
    for bad in [(0, 1, 1), (-1, 2, 2)]:
        try:
            solve_sss(*bad)
        except ValueError as e:
            print(f"SSS {bad} → {e}")

    print("all checks passed")
