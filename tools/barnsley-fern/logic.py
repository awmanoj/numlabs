"""Barnsley fern — the math of an Iterated Function System (IFS).

Unlike the Mandelbrot / Julia / Newton fractals (which ask, pixel by pixel,
"where does this point end up?"), the fern is drawn by the **chaos game**:

    start anywhere, then over and over pick one of a few affine maps at random
    (each with its own probability) and jump there, plotting every landing.

Astonishingly, those scattered dots converge onto one fixed shape — the
*attractor* of the maps — no matter where you start. For Barnsley's four maps
that attractor is a fern, leaflets and all. Each map is an affine transform

    x' = a*x + b*y + e
    y' = c*x + d*y + f

applied with probability p (the probabilities are chosen roughly in proportion
to each piece's area, so the dots spread evenly). The four maps do four jobs:
one draws the stem, one shrinks-and-rotates the whole fern up one notch, and two
spin off the bottom-left and bottom-right leaflets.

The page renders the fern in JavaScript (hundreds of thousands of points), but
this module is the source of truth: it defines the maps, the chaos-game step,
and — what the page actually calls through Pyodide — `describe_map`, the
geometric decomposition (scale, rotation, determinant) of each affine map.

Functions
- apply_map(m, x, y)         : one affine map applied to a point.
- normalize(maps)            : copy of maps with probabilities summing to 1.
- choose(maps, r)            : pick a map index from r in [0, 1).
- step(x, y, maps, r)        : one chaos-game step -> (x', y', map index).
- run(maps, n, skip, seed)   : generate points (x, y, map index).
- bounds(maps, n, seed)      : bounding box of the attractor.
- describe_map(m)            : scale / rotation / determinant of a map.
"""

import math
import random

# Each map: a, b, c, d, e, f (the affine transform) and p (its probability).
def _m(a, b, c, d, e, f, p):
    return {"a": a, "b": b, "c": c, "d": d, "e": e, "f": f, "p": p}


PRESETS = {
    "classic": {
        "label": "Classic Barnsley fern",
        "maps": [
            _m(0.00,  0.00,  0.00, 0.16, 0.00, 0.00, 0.01),   # stem
            _m(0.85,  0.04, -0.04, 0.85, 0.00, 1.60, 0.85),   # successively smaller leaflets
            _m(0.20, -0.26,  0.23, 0.22, 0.00, 1.60, 0.07),   # bottom-left leaflet
            _m(-0.15, 0.28,  0.26, 0.24, 0.00, 0.44, 0.07),   # bottom-right leaflet
        ],
    },
    "cyclosorus": {
        "label": "Cyclosorus fern",
        "maps": [
            _m(0.00,  0.00,  0.00,  0.25,  0.00, -0.40, 0.02),
            _m(0.95,  0.005, -0.005, 0.93, -0.002, 0.50, 0.84),
            _m(0.035, -0.20,  0.16,  0.04, -0.09,  0.02, 0.07),
            _m(-0.04,  0.20,  0.16,  0.04,  0.083, 0.12, 0.07),
        ],
    },
    "fishbone": {
        "label": "Fishbone fern",
        "maps": [
            _m(0.00,  0.00,  0.00,  0.25,  0.00, -0.40, 0.02),
            _m(0.95,  0.002, -0.002, 0.93, -0.002, 0.50, 0.84),
            _m(0.035, -0.11,  0.27,  0.01, -0.05,  0.005, 0.07),
            _m(-0.04,  0.11,  0.27,  0.01,  0.047, 0.06, 0.07),
        ],
    },
    "windswept": {
        # The classic fern with a stronger shear in the main map — it leans.
        "label": "Windswept fern (mutant)",
        "maps": [
            _m(0.00,  0.00,  0.00, 0.16, 0.00, 0.00, 0.01),
            _m(0.85,  0.12, -0.04, 0.85, 0.00, 1.60, 0.85),
            _m(0.20, -0.26,  0.23, 0.22, 0.00, 1.60, 0.07),
            _m(-0.15, 0.28,  0.26, 0.24, 0.00, 0.44, 0.07),
        ],
    },
}


def apply_map(m, x, y):
    """Apply one affine map to a point."""
    return (m["a"] * x + m["b"] * y + m["e"],
            m["c"] * x + m["d"] * y + m["f"])


def normalize(maps):
    """Return a copy of maps with probabilities renormalised to sum to 1.

    If every probability is zero, fall back to equal weights so the chaos game
    still runs.
    """
    total = sum(m["p"] for m in maps)
    out = []
    for m in maps:
        m2 = dict(m)
        m2["p"] = (m["p"] / total) if total > 0 else (1.0 / len(maps))
        out.append(m2)
    return out


def choose(maps, r):
    """Pick a map index from r in [0, 1) by cumulative probability."""
    maps = normalize(maps)
    acc = 0.0
    for i, m in enumerate(maps):
        acc += m["p"]
        if r < acc:
            return i
    return len(maps) - 1


def step(x, y, maps, r):
    """One chaos-game step: choose a map by r, apply it, report which."""
    idx = choose(maps, r)
    nx, ny = apply_map(maps[idx], x, y)
    return nx, ny, idx


def run(maps, n, skip=20, seed=1):
    """Generate n chaos-game points as (x, y, map index), skipping a transient."""
    maps = normalize(maps)
    rng = random.Random(seed)
    x = y = 0.0
    pts = []
    for i in range(n):
        x, y, idx = step(x, y, maps, rng.random())
        if i >= skip:
            pts.append((x, y, idx))
    return pts


def bounds(maps, n=20000, seed=1):
    """Bounding box (xmin, xmax, ymin, ymax) of the attractor."""
    pts = run(maps, n, skip=20, seed=seed)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), max(xs), min(ys), max(ys)


def describe_map(m):
    """Geometric decomposition of an affine map's linear part [[a, b], [c, d]].

    Returns determinant, the two singular values (max/min stretch factors),
    and the rotation angle of its polar-decomposition rotation, plus p. A map
    is contractive (the chaos game needs this) when its largest singular value
    is below 1.
    """
    a, b, c, d = m["a"], m["b"], m["c"], m["d"]
    det = a * d - b * c
    trace = a * a + b * b + c * c + d * d
    disc = math.sqrt(max(0.0, trace * trace - 4.0 * det * det))
    s_max = math.sqrt(max(0.0, (trace + disc) / 2.0))
    s_min = math.sqrt(max(0.0, (trace - disc) / 2.0))
    rotation = math.degrees(math.atan2(c - b, a + d))
    return {
        "det": det,
        "s_max": s_max,
        "s_min": s_min,
        "rotation": rotation,
        "p": m["p"],
        "contractive": s_max < 1.0,
    }


if __name__ == "__main__":
    classic = PRESETS["classic"]["maps"]

    # --- sanity checks -----------------------------------------------------
    # Probabilities renormalise to 1.
    assert abs(sum(m["p"] for m in normalize(classic)) - 1.0) < 1e-12

    # choose() respects the cumulative probabilities (stem is the first 1%).
    assert choose(classic, 0.005) == 0
    assert choose(classic, 0.5) == 1          # the 85% map
    assert choose(classic, 0.90) == 2
    assert choose(classic, 0.97) == 3

    # The classic fern sits roughly in x in [-2.8, 2.8], y in [0, ~10].
    xmin, xmax, ymin, ymax = bounds(classic)
    assert -3.0 < xmin and xmax < 3.0
    assert -0.05 < ymin and 9.0 < ymax < 11.0

    # All four maps are contractions (largest singular value < 1).
    assert all(describe_map(m)["contractive"] for m in classic)

    # The 85% map barely shrinks (s_max ~ 0.85) and barely rotates.
    d2 = describe_map(classic[1])
    assert 0.84 < d2["s_max"] < 0.87 and abs(d2["rotation"]) < 6

    print("Barnsley fern logic — all sanity checks passed.\n")

    # A tiny ASCII fern, plotted from the chaos game.
    GW, GH = 60, 32
    grid = [[" "] * GW for _ in range(GH)]
    pts = run(classic, 40000)
    xmin, xmax, ymin, ymax = bounds(classic)
    for x, y, _ in pts:
        gx = int((x - xmin) / (xmax - xmin) * (GW - 1))
        gy = int((y - ymin) / (ymax - ymin) * (GH - 1))
        grid[GH - 1 - gy][gx] = "*"
    print(PRESETS["classic"]["label"] + "\n")
    print("\n".join("".join(row) for row in grid))
