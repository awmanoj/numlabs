"""Julia sets — pure-Python math behind the explorer.

A Julia set is the twin of the Mandelbrot set. Both use the very same iteration

    z(n+1) = z(n)^2 + c

but they vary a different knob:

- Mandelbrot: always start at z(0) = 0 and sweep the *parameter* c over the plane.
- Julia: *fix* one c, and sweep the *starting value* z(0) over the plane.

So every point c of the Mandelbrot set is the recipe for one whole Julia set.
The filled Julia set for a given c is the set of starting points z whose orbit
stays bounded forever; the page paints those black and colours the escapees by
how fast they leave (the same |z| > 2 escape-time idea as the Mandelbrot tool).

There is a beautiful dichotomy (Fatou–Julia): if c lies *inside* the Mandelbrot
set the Julia set is a single connected piece; if c lies *outside*, it shatters
into a totally disconnected dust of points. `is_connected` reports which.

The page renders the picture in JavaScript for speed, but this module is the
source of truth for the math and is what the point inspector calls directly.

Functions
- escape(zr, zi, cr, ci, max_iter, bailout) : full escape result for a start z.
- escape_count(zr, zi, cr, ci, max_iter)    : just the integer iteration count.
- orbit(zr, zi, cr, ci, steps)              : the first few z values of the orbit.
- mandel_escape_count(cr, ci, max_iter)     : escape count of c from 0 (for M).
- is_connected(cr, ci, max_iter)            : is the Julia set for c connected?
- describe_c(cr, ci, max_iter)              : connectivity verdict for a c.
- classify(zr, zi, cr, ci, max_iter)        : verdict for one starting point z.
"""

import math

DEFAULT_MAX_ITER = 200
BAILOUT = 2.0


def escape(zr, zi, cr, ci, max_iter=DEFAULT_MAX_ITER, bailout=BAILOUT):
    """Iterate z -> z^2 + c from the given start z, with c fixed.

    Returns a dict:
        escaped    : did |z| cross the bailout within max_iter steps?
        iterations : steps taken (== max_iter if it never escaped)
        smooth     : fractional escape value for smooth colouring, or None
        zr, zi     : the final z
        abs_z      : |z| at the stopping point

    Smooth value: mu = n + 1 - log2(log|z|), the normalised iteration count
    that removes the visible colour bands of the bare integer count.
    """
    bail_sq = bailout * bailout
    n = 0
    while n < max_iter:
        zr2 = zr * zr
        zi2 = zi * zi
        if zr2 + zi2 > bail_sq:
            break
        zi = 2.0 * zr * zi + ci
        zr = zr2 - zi2 + cr
        n += 1

    abs_z = math.hypot(zr, zi)
    escaped = (zr * zr + zi * zi) > bail_sq
    smooth = None
    if escaped and abs_z > 1.0:
        smooth = n + 1.0 - math.log(math.log(abs_z)) / math.log(2.0)
    return {
        "escaped": escaped,
        "iterations": n,
        "smooth": smooth,
        "zr": zr,
        "zi": zi,
        "abs_z": abs_z,
    }


def escape_count(zr, zi, cr, ci, max_iter=DEFAULT_MAX_ITER, bailout=BAILOUT):
    """Integer escape iteration count for start z (== max_iter if bounded)."""
    return escape(zr, zi, cr, ci, max_iter, bailout)["iterations"]


def orbit(zr, zi, cr, ci, steps=12, bailout=BAILOUT):
    """The first `steps` points of the orbit z(0..steps-1), as (zr, zi) pairs.

    Stops early once the orbit escapes past the bailout, so the list can be
    shorter than `steps`.
    """
    bail_sq = bailout * bailout
    pts = []
    for _ in range(max(0, steps)):
        pts.append((zr, zi))
        if zr * zr + zi * zi > bail_sq:
            break
        zr, zi = zr * zr - zi * zi + cr, 2.0 * zr * zi + ci
    return pts


def mandel_escape_count(cr, ci, max_iter=DEFAULT_MAX_ITER, bailout=BAILOUT):
    """Escape count of c under the Mandelbrot iteration (start z = 0).

    Used to decide connectivity: c is in the Mandelbrot set exactly when this
    orbit stays bounded.
    """
    return escape(0.0, 0.0, cr, ci, max_iter, bailout)["iterations"]


def is_connected(cr, ci, max_iter=DEFAULT_MAX_ITER, bailout=BAILOUT):
    """True if the Julia set for c is connected (i.e. c is in the Mandelbrot set).

    Outside the Mandelbrot set the Julia set is a disconnected Cantor dust.
    """
    return not escape(0.0, 0.0, cr, ci, max_iter, bailout)["escaped"]


def describe_c(cr, ci, max_iter=DEFAULT_MAX_ITER, bailout=BAILOUT):
    """Connectivity verdict for a parameter c, for the picker read-out."""
    connected = is_connected(cr, ci, max_iter, bailout)
    if connected:
        verdict = "c is in the Mandelbrot set → connected Julia set."
    else:
        verdict = "c is outside the Mandelbrot set → dust (disconnected)."
    return {"cr": cr, "ci": ci, "connected": connected, "verdict": verdict}


def classify(zr, zi, cr, ci, max_iter=DEFAULT_MAX_ITER, bailout=BAILOUT):
    """A friendly verdict for one starting point z, for the inspector panel."""
    res = escape(zr, zi, cr, ci, max_iter, bailout)
    if not res["escaped"]:
        verdict = f"In the filled Julia set — bounded after {max_iter} iterations."
    elif res["iterations"] <= 2:
        verdict = "Far outside — escapes almost immediately."
    elif res["iterations"] < max_iter * 0.1:
        verdict = "Outside the set — escapes quickly."
    else:
        verdict = "Right on the Julia boundary — clings before escaping."
    res = dict(res)
    res["verdict"] = verdict
    res["max_iter"] = max_iter
    return res


if __name__ == "__main__":
    # --- sanity checks -----------------------------------------------------
    # c = 0: the iteration is just z -> z^2, whose filled Julia set is the
    # closed unit disc. Points inside the unit circle stay bounded; outside
    # they blow up.
    assert not escape(0.5, 0.0, 0.0, 0.0)["escaped"]
    assert escape(1.5, 0.0, 0.0, 0.0)["escaped"]
    assert escape_count(0.0, 0.0, 0.0, 0.0) == DEFAULT_MAX_ITER

    # Connectivity dichotomy: c = 0 is in the Mandelbrot set (connected);
    # c = 1 + 1i is well outside it (dust).
    assert is_connected(0.0, 0.0)
    assert not is_connected(1.0, 1.0)

    # The Douady rabbit (c = -0.123 + 0.745i) is a connected Julia set.
    assert is_connected(-0.123, 0.745)

    # Smooth value sits just above the integer count when a point escapes.
    e = escape(1.5, 0.0, 0.0, 0.0)
    assert e["escaped"] and e["smooth"] is not None
    assert e["iterations"] <= e["smooth"] < e["iterations"] + 2

    # Orbit of a member stays bounded; orbit of an escapee grows past 2.
    assert all(zr * zr + zi * zi <= 4.0 for zr, zi in orbit(0.5, 0.0, 0.0, 0.0, 8))
    assert any(zr * zr + zi * zi > 4.0 for zr, zi in orbit(1.5, 0.0, 0.0, 0.0, 8))

    print("Julia logic — all sanity checks passed.\n")

    # A tiny ASCII portrait of the Douady rabbit, just to eyeball the shape.
    CR, CI = -0.123, 0.745
    rows = []
    for iy in range(22):
        zi = 1.3 - iy * (2.6 / 21)
        line = []
        for ix in range(64):
            zr = -1.6 + ix * (3.2 / 63)
            line.append(" " if escape_count(zr, zi, CR, CI, 80) == 80 else ".")
        rows.append("".join(line))
    print(f"Douady rabbit  c = {CR} + {CI}i\n")
    print("\n".join(rows))
