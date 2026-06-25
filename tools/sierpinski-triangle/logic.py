"""Sierpinski triangle — one fractal, reached three completely different ways.

The Sierpinski triangle (Sierpiński, 1915) is the canonical fractal: a triangle
with its middle quarter removed, then the same done to each surviving triangle,
forever. What makes it a wonderful teaching object is that you can arrive at the
*exact same shape* from routes that look utterly unrelated:

1. **Recursive subdivision** — the deterministic, "obvious" construction. Split a
   triangle into four half-size triangles and throw away the middle one; recurse
   on the three survivors. `subdivide(tri, depth)` does this.

2. **The chaos game** — pure randomness. Drop a point anywhere, then repeatedly
   pick one of the three corners at random and step *halfway* toward it, plotting
   each landing. The random dots pile up into the Sierpinski triangle and nothing
   else. `run(...)` plays this game. This is the "order out of chaos" surprise:
   a fair die, applied a million times, paints a perfectly structured fractal.

3. **Pascal's triangle, odd vs. even** — no geometry at all. Colour every odd
   binomial coefficient and the Sierpinski pattern falls out of arithmetic.
   `pascal_mod2(rows)` produces it.

That three such different processes — recursion, chance, and number theory —
converge on one shape is the heart of why fractals feel like a law of nature
rather than a drawing. This module is the source of truth for all three, plus
the counting facts (how many triangles, how much area survives) and the
similarity dimension log3/log2 ≈ 1.585 that says the figure is "between" a line
and a filled area.

Functions
- midpoint(p, q)                 : the point halfway between two points.
- chaos_step(x, y, vx, vy, r)    : step a fraction r from (x,y) toward a corner.
- choose_vertex(rng, n)          : pick one of n corners uniformly.
- run(vertices, n, ratio, ...)   : chaos-game points (x, y, corner index).
- bounds(vertices)               : bounding box of the corners.
- subdivide(tri, depth)          : list of surviving triangles at a given depth.
- count_triangles(depth)         : 3**depth.
- area_fraction(depth)           : (3/4)**depth — share of the original area left.
- triangle_area(tri)             : area of one triangle.
- similarity_dimension(...)      : log(copies)/log(1/ratio); 3 halves -> log3/log2.
- pascal_mod2(rows)              : Pascal's triangle reduced mod 2 (1 = odd).
- depth_facts(depth)             : the counting facts for a depth (used by the page).
"""

import math
import random

# A roughly equilateral triangle, apex up, in a unit-ish box. The chaos game and
# the subdivision both live inside this hull, so it doubles as the default frame.
VERTICES = [
    (0.0, 1.0),                                   # apex
    (-math.sqrt(3) / 2.0, -0.5),                  # bottom-left
    (math.sqrt(3) / 2.0, -0.5),                   # bottom-right
]


def midpoint(p, q):
    """The point exactly halfway between p and q."""
    return ((p[0] + q[0]) / 2.0, (p[1] + q[1]) / 2.0)


def chaos_step(x, y, vx, vy, ratio=0.5):
    """Move from (x, y) a fraction `ratio` of the way toward corner (vx, vy).

    For the Sierpinski triangle the magic ratio is 1/2: with three corners and
    half-steps the random walk fills exactly the gasket. (Other ratios / corner
    counts make other gaskets — e.g. 4 corners at ratio 1/2 just fills a square,
    which is why the *carpet* needs a different rule.)
    """
    return (x + (vx - x) * ratio, y + (vy - y) * ratio)


def choose_vertex(rng, n):
    """Pick one of n corners uniformly at random."""
    return rng.randrange(n)


def run(vertices, n, ratio=0.5, skip=10, seed=1):
    """Play the chaos game for n steps; return points as (x, y, corner index).

    Starts at the centroid, skips a short transient, and is fully deterministic
    for a given seed so the page can reproduce a render exactly.
    """
    rng = random.Random(seed)
    cx = sum(v[0] for v in vertices) / len(vertices)
    cy = sum(v[1] for v in vertices) / len(vertices)
    x, y = cx, cy
    pts = []
    for i in range(n):
        vi = choose_vertex(rng, len(vertices))
        vx, vy = vertices[vi]
        x, y = chaos_step(x, y, vx, vy, ratio)
        if i >= skip:
            pts.append((x, y, vi))
    return pts


def bounds(vertices):
    """Bounding box (xmin, xmax, ymin, ymax) of the corners."""
    xs = [v[0] for v in vertices]
    ys = [v[1] for v in vertices]
    return min(xs), max(xs), min(ys), max(ys)


def subdivide(tri, depth):
    """Surviving triangles after `depth` rounds of removing the middle triangle.

    `tri` is a 3-tuple of (x, y) corners. depth 0 returns [tri] unchanged. Each
    round replaces every triangle with the three corner sub-triangles (the
    central one is dropped), so the count is 3**depth.
    """
    if depth <= 0:
        return [tri]
    a, b, c = tri
    ab, bc, ca = midpoint(a, b), midpoint(b, c), midpoint(c, a)
    children = [
        (a, ab, ca),     # corner at a
        (ab, b, bc),     # corner at b
        (ca, bc, c),     # corner at c
    ]
    out = []
    for child in children:
        out.extend(subdivide(child, depth - 1))
    return out


def count_triangles(depth):
    """How many filled triangles survive at this depth: 3**depth."""
    return 3 ** depth


def area_fraction(depth):
    """Share of the original triangle's area still filled: (3/4)**depth.

    Each round keeps 3 of 4 quarter-triangles, so the filled area shrinks by 3/4
    every step and tends to zero — the limit shape has zero area yet infinite
    perimeter.
    """
    return (3.0 / 4.0) ** depth


def triangle_area(tri):
    """Area of one triangle via the shoelace formula."""
    (x1, y1), (x2, y2), (x3, y3) = tri
    return abs((x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1)) / 2.0


def similarity_dimension(copies=3, ratio=0.5):
    """Hausdorff/similarity dimension log(copies)/log(1/ratio).

    The gasket is 3 copies of itself each scaled by 1/2, so the dimension is
    log3/log2 ≈ 1.585 — strictly between a 1-D line and a 2-D area.
    """
    return math.log(copies) / math.log(1.0 / ratio)


def pascal_mod2(rows):
    """Pascal's triangle reduced mod 2: a list of rows of 0/1 (1 = odd entry).

    Plotting the 1s (e.g. left-aligned and read as a triangle) reproduces the
    Sierpinski pattern — a third, purely arithmetic, route to the same fractal.
    """
    out = []
    row = [1]
    for _ in range(rows):
        out.append(row[:])
        nxt = [1]
        for i in range(len(row) - 1):
            nxt.append((row[i] + row[i + 1]) & 1)
        nxt.append(1)
        row = nxt
    return out


def depth_facts(depth):
    """Counting facts for one depth — what the page's stats table shows.

    Returns the number of triangles, the area still filled (fraction and
    percent), and the constant similarity dimension.
    """
    return {
        "depth": depth,
        "triangles": count_triangles(depth),
        "area_fraction": area_fraction(depth),
        "area_percent": area_fraction(depth) * 100.0,
        "dimension": similarity_dimension(),
    }


if __name__ == "__main__":
    # --- sanity checks -----------------------------------------------------
    # midpoint is the average of the two points.
    assert midpoint((0, 0), (2, 4)) == (1.0, 2.0)

    # A half-step toward a corner lands halfway there.
    assert chaos_step(0.0, 0.0, 1.0, 0.0, 0.5) == (0.5, 0.0)

    # Subdivision counts: 3**depth triangles, none in the middle.
    for d in range(0, 7):
        assert len(subdivide((VERTICES[0], VERTICES[1], VERTICES[2]), d)) == count_triangles(d)
    assert count_triangles(5) == 243

    # Area really does shrink by 3/4 each round, summing the sub-triangles back
    # up to (3/4)**depth of the whole.
    whole = triangle_area((VERTICES[0], VERTICES[1], VERTICES[2]))
    for d in range(0, 6):
        kept = sum(triangle_area(t) for t in subdivide(tuple(VERTICES), d))
        assert abs(kept - whole * area_fraction(d)) < 1e-9

    # The similarity dimension is log3/log2.
    assert abs(similarity_dimension() - math.log(3) / math.log(2)) < 1e-12
    assert 1.58 < similarity_dimension() < 1.59

    # Chaos game is deterministic for a seed and stays inside the triangle hull.
    pts = run(VERTICES, 5000, seed=7)
    xmin, xmax, ymin, ymax = bounds(VERTICES)
    assert all(xmin - 1e-9 <= x <= xmax + 1e-9 and ymin - 1e-9 <= y <= ymax + 1e-9
               for x, y, _ in pts)
    assert run(VERTICES, 100, seed=7) == run(VERTICES, 100, seed=7)

    # Pascal mod 2: row 4 is 1 0 0 0 1 (C(4,1..3) are all even).
    p = pascal_mod2(8)
    assert p[4] == [1, 0, 0, 0, 1]
    assert all(p[i][0] == 1 and p[i][-1] == 1 for i in range(len(p)))

    print("Sierpinski triangle logic — all sanity checks passed.\n")

    # Two ASCII portraits of the same fractal: chaos game, then Pascal mod 2.
    GW, GH = 63, 32
    grid = [[" "] * GW for _ in range(GH)]
    for x, y, _ in run(VERTICES, 40000, seed=1):
        gx = int((x - xmin) / (xmax - xmin) * (GW - 1))
        gy = int((y - ymin) / (ymax - ymin) * (GH - 1))
        grid[GH - 1 - gy][gx] = "*"
    print("Route 1 — the chaos game (random half-steps to a corner):\n")
    print("\n".join("".join(row) for row in grid))

    print("\nRoute 2 — Pascal's triangle, odd entries only:\n")
    rows = pascal_mod2(32)
    for i, r in enumerate(rows):
        pad = " " * (len(rows) - i)
        print(pad + " ".join("*" if v else " " for v in r))
