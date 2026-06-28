"""Koch snowflake — pure-Python logic.

The Koch snowflake is built by *edge replacement*. Start with an equilateral
triangle. Then, over and over, replace every straight edge with four edges:
cut the edge into thirds and pop an equilateral bump out of the middle third.

    A ─────────── B        becomes        A ──C   E── B
                                                ╲ ╱
                                                 D          (D is the bump apex)

Three flavours, all from the same rule — they differ only in which way each
bump points:

  * **classic**  — every bump points outward  → the snowflake (perfect order)
  * **anti**     — every bump points inward    → the Koch anti-snowflake
  * **random**   — each bump flips a coin       → an organic coastline

The hot drawing loop lives in JS (it just strokes the line list); this module
is the source of truth for the geometry and the numbers shown on the page:
``build`` generates the point list, ``metrics`` gives the segment count,
perimeter, area and the fractal dimension. A ``__main__`` block sanity-checks
the construction and prints an ASCII snowflake.
"""

import math
import random

ANGLE = math.pi / 3  # 60° — the equilateral bump


def _equilateral_triangle(side=1.0):
    """An equilateral triangle centred on the origin, listed counter-clockwise."""
    r = side / math.sqrt(3)                     # circumradius
    return [(r * math.cos(math.pi / 2 + k * 2 * math.pi / 3),
             r * math.sin(math.pi / 2 + k * 2 * math.pi / 3))
            for k in range(3)]


def _apex(c, e, sign):
    """The bump apex: rotate the vector c→e by ``sign·60°`` about ``c``.

    Because |c→e| is one third of the original edge, a 60° rotation lands on
    the far vertex of the equilateral triangle sitting on that third.
    """
    dx, dy = e[0] - c[0], e[1] - c[1]
    a = sign * ANGLE
    ca, sa = math.cos(a), math.sin(a)
    return (c[0] + dx * ca - dy * sa, c[1] + dx * sa + dy * ca)


def _centroid(pts):
    n = len(pts)
    return (sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n)


def _d2(p, q):
    return (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2


def _outward_sign(pts):
    """Which rotation sign (+1/−1) makes a bump point *away* from the centre.

    Computed once from the starting polygon; edge-replacement preserves the
    winding, so the same sign means "outward" at every later iteration.
    """
    cen = _centroid(pts)
    a, b = pts[0], pts[1]
    c = (a[0] + (b[0] - a[0]) / 3, a[1] + (b[1] - a[1]) / 3)
    e = (a[0] + 2 * (b[0] - a[0]) / 3, a[1] + 2 * (b[1] - a[1]) / 3)
    return 1 if _d2(_apex(c, e, 1), cen) > _d2(_apex(c, e, -1), cen) else -1


def _iterate(pts, base, mode, rng):
    """One round of edge replacement over a closed polygon."""
    n = len(pts)
    out = []
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        c = (a[0] + (b[0] - a[0]) / 3, a[1] + (b[1] - a[1]) / 3)
        e = (a[0] + 2 * (b[0] - a[0]) / 3, a[1] + 2 * (b[1] - a[1]) / 3)
        if mode == "classic":
            sign = base
        elif mode == "anti":
            sign = -base
        else:                                   # random
            sign = rng.choice((base, -base))
        out.append(a)
        out.append(c)
        out.append(_apex(c, e, sign))
        out.append(e)
    return out


def build(iterations, mode="classic", seed=0, side=1.0):
    """Return the closed list of (x, y) points after ``iterations`` rounds.

    ``mode`` is ``"classic"``, ``"anti"`` or ``"random"``. ``seed`` makes the
    random flavour reproducible.
    """
    if iterations < 0:
        raise ValueError("iterations must be 0 or more")
    if mode not in ("classic", "anti", "random"):
        raise ValueError("mode must be 'classic', 'anti' or 'random'")
    pts = _equilateral_triangle(side)
    base = _outward_sign(pts)
    rng = random.Random(seed)
    for _ in range(iterations):
        pts = _iterate(pts, base, mode, rng)
    return pts


def polygon_area(pts):
    """Shoelace area (absolute) of a closed polygon."""
    n = len(pts)
    s = 0.0
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2


def polygon_perimeter(pts):
    n = len(pts)
    return sum(math.dist(pts[i], pts[(i + 1) % n]) for i in range(n))


def metrics(iterations, side=1.0):
    """Closed-form facts about the *classic* snowflake at iteration n.

    perimeter = 3·side·(4/3)ⁿ  (grows without bound),
    area      = area₀·(8/5 − 3/5·(4/9)ⁿ)  (converges to 8/5·area₀),
    dimension = log4 / log3 ≈ 1.2619.
    """
    n = iterations
    area0 = math.sqrt(3) / 4 * side ** 2
    return {
        "iterations": n,
        "segments": 3 * 4 ** n,
        "perimeter": 3 * side * (4 / 3) ** n,
        "area": area0 * (8 / 5 - 3 / 5 * (4 / 9) ** n),
        "limit_area": area0 * 8 / 5,
        "dimension": math.log(4) / math.log(3),
    }


def build_json(iterations, mode, seed):
    """Point list as a flat JSON array [x0,y0,x1,y1,…] — compact for the browser."""
    import json
    flat = []
    for x, y in build(iterations, mode, seed):
        flat.append(round(x, 6))
        flat.append(round(y, 6))
    return json.dumps(flat)


def metrics_json(iterations):
    import json
    return json.dumps(metrics(iterations))


def _ascii(iterations=3, width=72):
    """Render the classic snowflake as ASCII art for the __main__ demo."""
    pts = build(iterations, "classic")
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    height = max(8, int(width * (maxy - miny) / (maxx - minx) / 2))
    grid = [[" "] * width for _ in range(height)]
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        steps = 1 + int(math.dist(a, b) / (maxx - minx) * width)
        for s in range(steps + 1):
            t = s / steps
            x = a[0] + (b[0] - a[0]) * t
            y = a[1] + (b[1] - a[1]) * t
            gx = int((x - minx) / (maxx - minx) * (width - 1))
            gy = int((maxy - y) / (maxy - miny) * (height - 1))
            grid[gy][gx] = "*"
    return "\n".join("".join(row) for row in grid)


if __name__ == "__main__":
    # Segment / point counts: 3·4ⁿ edges, one point per edge in the closed list.
    for n in range(5):
        pts = build(n)
        assert len(pts) == 3 * 4 ** n, (n, len(pts))
        assert metrics(n)["segments"] == 3 * 4 ** n
    print("segment counts:", [metrics(n)["segments"] for n in range(6)])

    # Classic geometry matches the closed forms (perimeter and area).
    for n in range(6):
        pts = build(n)
        m = metrics(n)
        assert abs(polygon_perimeter(pts) - m["perimeter"]) < 1e-9, n
        assert abs(polygon_area(pts) - m["area"]) < 1e-9, n
    # Area rises toward 8/5 of the triangle but never reaches it.
    a0, a5, lim = metrics(0)["area"], metrics(5)["area"], metrics(0)["limit_area"]
    assert a0 < a5 < lim
    print(f"area: n0={a0:.5f}  n5={a5:.5f}  limit(8/5·a0)={lim:.5f}")

    # Each bump really is equilateral: |c-d| = |e-d| = |c-e|.
    p = build(1)
    a, c, d, e = p[0], p[1], p[2], p[3]
    assert abs(math.dist(c, d) - math.dist(e, d)) < 1e-9
    assert abs(math.dist(c, d) - math.dist(c, e)) < 1e-9

    # Anti-snowflake eats area; classic adds it.
    assert polygon_area(build(3, "anti")) < polygon_area(build(0))
    assert polygon_area(build(3, "classic")) > polygon_area(build(0))

    # Random is reproducible per seed and differs across seeds.
    assert build(4, "random", seed=1) == build(4, "random", seed=1)
    assert build(4, "random", seed=1) != build(4, "random", seed=2)

    # Dimension
    assert abs(metrics(0)["dimension"] - 1.261859) < 1e-6
    print(f"fractal dimension = {metrics(0)['dimension']:.6f}")

    # Errors
    for bad in (dict(iterations=-1), dict(iterations=2, mode="spiral")):
        try:
            build(**bad)
            raise AssertionError("expected failure")
        except ValueError as ex:
            print("rejected:", ex)

    print()
    print(_ascii(3))
    print("\nall checks passed")
