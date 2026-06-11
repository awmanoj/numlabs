"""Mandelbrot set — pure-Python math behind the explorer.

The Mandelbrot set M is the set of complex numbers c for which the iteration

    z(0) = 0,    z(n+1) = z(n)^2 + c

stays bounded forever. In practice a point has escaped to infinity the moment
|z| exceeds the bailout radius 2: once |z| > 2 the orbit provably diverges, so
we can stop early. Points that never cross the bailout within `max_iter` steps
are treated as members of the set (coloured black on the page).

The page renders the picture in JavaScript for speed — hundreds of thousands of
pixels per frame — but this module is the source of truth for the math, and the
page calls it directly (through Pyodide) for the single-point "inspect" panel:
the orbit of z, the escape count, and the smooth (fractional) escape value used
for banding-free colouring.

Functions
- escape(cx, cy, max_iter, bailout) : full escape result for one point c.
- escape_count(cx, cy, max_iter)    : just the integer iteration count.
- orbit(cx, cy, steps)              : the first few z values of the orbit.
- in_main_cardioid(cx, cy)          : interior test for the big heart.
- in_period2_bulb(cx, cy)           : interior test for the left disc.
- classify(cx, cy, max_iter)        : a friendly human verdict for a point.
"""

import math

DEFAULT_MAX_ITER = 200
BAILOUT = 2.0
BAILOUT_SQ = BAILOUT * BAILOUT


def in_main_cardioid(cx, cy):
    """True if c is inside the main cardioid (the big heart-shaped body).

    Every point in here is in the set, so the renderer can skip iterating it.
    Derived from the cardioid's parametric form: a point is inside when
    q*(q + (x - 1/4)) <= y^2/4, with q = (x - 1/4)^2 + y^2.
    """
    x = cx - 0.25
    q = x * x + cy * cy
    return q * (q + x) <= 0.25 * cy * cy


def in_period2_bulb(cx, cy):
    """True if c is inside the period-2 bulb (the disc on the left, centre -1).

    It is the circle of radius 1/4 about -1: (x + 1)^2 + y^2 <= 1/16.
    """
    dx = cx + 1.0
    return dx * dx + cy * cy <= 0.0625


def escape(cx, cy, max_iter=DEFAULT_MAX_ITER, bailout=BAILOUT):
    """Iterate z -> z^2 + c from z = 0 and report what happened.

    Returns a dict:
        escaped    : did |z| cross the bailout within max_iter steps?
        iterations : steps taken (== max_iter if it never escaped)
        smooth     : fractional escape value (iterations + a sub-step
                     correction) for smooth colouring; None if it didn't escape
        zr, zi     : the final z
        abs_z      : |z| at the stopping point

    The smooth value uses the normalised iteration count
        mu = n + 1 - log2( log|z| )
    which removes the visible bands you get from the bare integer count.
    """
    bail_sq = bailout * bailout
    zr = 0.0
    zi = 0.0
    n = 0
    while n < max_iter:
        zr2 = zr * zr
        zi2 = zi * zi
        if zr2 + zi2 > bail_sq:
            break
        zi = 2.0 * zr * zi + cy
        zr = zr2 - zi2 + cx
        n += 1

    abs_z = math.hypot(zr, zi)
    escaped = (zr * zr + zi * zi) > bail_sq
    smooth = None
    if escaped and abs_z > 1.0:
        # n + 1 - log2(log|z|); guard against log of a value <= 1.
        smooth = n + 1.0 - math.log(math.log(abs_z)) / math.log(2.0)
    return {
        "escaped": escaped,
        "iterations": n,
        "smooth": smooth,
        "zr": zr,
        "zi": zi,
        "abs_z": abs_z,
    }


def escape_count(cx, cy, max_iter=DEFAULT_MAX_ITER, bailout=BAILOUT):
    """Integer escape iteration count for c (== max_iter if it stays bounded)."""
    return escape(cx, cy, max_iter, bailout)["iterations"]


def orbit(cx, cy, steps=12, bailout=BAILOUT):
    """The first `steps` points of the orbit z(0..steps-1), as (zr, zi) pairs.

    Stops early once the orbit escapes past the bailout (the next squaring
    would blow the numbers up), so the list can be shorter than `steps`.
    """
    bail_sq = bailout * bailout
    pts = []
    zr = 0.0
    zi = 0.0
    for _ in range(max(0, steps)):
        pts.append((zr, zi))
        if zr * zr + zi * zi > bail_sq:
            break
        zr, zi = zr * zr - zi * zi + cx, 2.0 * zr * zi + cy
    return pts


def classify(cx, cy, max_iter=DEFAULT_MAX_ITER, bailout=BAILOUT):
    """A friendly verdict for a single point c, for the inspector panel."""
    if in_main_cardioid(cx, cy):
        region = "inside the main cardioid"
    elif in_period2_bulb(cx, cy):
        region = "inside the period-2 bulb"
    else:
        region = None

    res = escape(cx, cy, max_iter, bailout)
    if not res["escaped"]:
        where = f" ({region})" if region else ""
        verdict = f"In the set — bounded after {max_iter} iterations{where}."
    elif res["iterations"] <= 2:
        verdict = "Far outside — escapes almost immediately."
    elif res["iterations"] < max_iter * 0.1:
        verdict = "Outside the set — escapes quickly."
    else:
        verdict = "Just outside — clings to the boundary before escaping."

    res = dict(res)
    res["region"] = region
    res["verdict"] = verdict
    res["max_iter"] = max_iter
    return res


if __name__ == "__main__":
    # --- sanity checks -----------------------------------------------------
    # The origin is the centre of the set and never escapes.
    assert not escape(0.0, 0.0)["escaped"]
    assert escape_count(0.0, 0.0) == DEFAULT_MAX_ITER

    # -1 is in the set (period-2 cycle 0 -> -1 -> 0 -> ...).
    assert not escape(-1.0, 0.0)["escaped"]

    # 2 escapes on the very first step; 0.5 escapes quickly.
    assert escape(2.0, 0.0)["escaped"]
    assert escape(0.5, 0.0)["escaped"]

    # Interior tests: 0 is in the cardioid, -1 in the period-2 bulb.
    assert in_main_cardioid(0.0, 0.0)
    assert in_period2_bulb(-1.0, 0.0)
    assert not in_main_cardioid(1.0, 1.0)

    # Smooth value sits just above the integer count when a point escapes.
    e = escape(0.4, 0.4)
    assert e["escaped"] and e["smooth"] is not None
    assert e["iterations"] <= e["smooth"] < e["iterations"] + 2

    # Orbit of a member stays bounded; orbit of an escapee grows past 2.
    assert all(zr * zr + zi * zi <= 4.0 for zr, zi in orbit(0.0, 0.0, 8))
    assert any(zr * zr + zi * zi > 4.0 for zr, zi in orbit(1.0, 1.0, 8))

    print("Mandelbrot logic — all sanity checks passed.\n")

    # A tiny ASCII portrait, just to eyeball the shape.
    rows = []
    for iy in range(22):
        cy = 1.1 - iy * (2.2 / 21)
        line = []
        for ix in range(64):
            cx = -2.2 + ix * (3.0 / 63)
            line.append(" " if escape_count(cx, cy, 60) == 60 else ".")
        rows.append("".join(line))
    print("\n".join(rows))
