"""Newton fractals — pure-Python math behind the explorer.

Newton's method is the classic way to chase down a root of a function: from a
guess z, step to

    z  ->  z - p(z) / p'(z)

and repeat. For a real function on a line it just converges. But run it on the
*complex* plane and colour every starting point by *which* root it ends up at,
and the basins of attraction interlock in an infinitely detailed fractal — the
boundary between "this point falls to root A" and "root B" is never smooth.

This module iterates a handful of polynomials (z^3 - 1 and friends), reports
which root a start point converges to and how fast, and exposes the orbit for
the inspector. A relaxation factor `a` generalises the step to
z -> z - a * p/p'; a = 1 is ordinary Newton, other values warp the basins.

Some starting points never settle — most famously z^3 - 2z + 2, where Newton's
method can fall into an attracting 0 -> 1 -> 0 cycle. Those are reported as not
converged (the page paints them black).

The page renders the picture in JavaScript for speed; this module is the source
of truth for the math and backs the point inspector.

Polynomials are stored as coefficient lists in *descending* powers, e.g.
z^3 - 1 is [1, 0, 0, -1]. `POLYS` also caches each one's roots.

Functions
- newton(zr, zi, poly, max_iter, tol, a) : which root a start converges to.
- orbit(zr, zi, poly, steps, a)          : the Newton iterates from a start.
- classify(zr, zi, poly, max_iter, a)    : a friendly verdict for a point.
- roots_of(poly)                         : the polynomial's roots as (re, im).
"""

import cmath

DEFAULT_MAX_ITER = 50
TOL = 1e-6

# Each polynomial: coefficients in descending powers, and its roots.
POLYS = {
    "cubic": {
        "label": "z^3 - 1",
        "coeffs": [1, 0, 0, -1],
        "roots": [
            (1.0, 0.0),
            (-0.5, 0.8660254037844387),
            (-0.5, -0.8660254037844387),
        ],
    },
    "quartic": {
        "label": "z^4 - 1",
        "coeffs": [1, 0, 0, 0, -1],
        "roots": [(1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0)],
    },
    "quintic": {
        "label": "z^5 - 1",
        "coeffs": [1, 0, 0, 0, 0, -1],
        "roots": [
            (1.0, 0.0),
            (0.30901699437494745, 0.9510565162951535),
            (-0.8090169943749475, 0.5877852522924731),
            (-0.8090169943749475, -0.5877852522924731),
            (0.30901699437494745, -0.9510565162951535),
        ],
    },
    "tricky": {
        # The textbook trap: Newton can fall into a 0 -> 1 -> 0 cycle here.
        "label": "z^3 - 2z + 2",
        "coeffs": [1, 0, -2, 2],
        "roots": [
            (-1.7692923542386314, 0.0),
            (0.8846461771193157, 0.5897428050222054),
            (0.8846461771193157, -0.5897428050222054),
        ],
    },
    "octic": {
        "label": "z^8 + 15z^4 - 16",
        "coeffs": [1, 0, 0, 0, 15, 0, 0, 0, -16],
        "roots": [
            (1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0),
            (1.4142135623730951, 1.4142135623730951),
            (-1.4142135623730951, 1.4142135623730951),
            (-1.4142135623730951, -1.4142135623730951),
            (1.4142135623730951, -1.4142135623730951),
        ],
    },
}


def roots_of(poly):
    """The roots of the polynomial as a list of (re, im) pairs."""
    return POLYS[poly]["roots"]


def _polyval(coeffs, z):
    """Evaluate a polynomial (descending-power coeffs) at z via Horner."""
    acc = 0j
    for c in coeffs:
        acc = acc * z + c
    return acc


def _deriv(coeffs):
    """Coefficients of the derivative, in descending powers."""
    n = len(coeffs) - 1
    return [coeffs[i] * (n - i) for i in range(n)]


def newton(zr, zi, poly="cubic", max_iter=DEFAULT_MAX_ITER, tol=TOL, a=1.0):
    """Run generalised Newton (z -> z - a*p/p') from a start point.

    Returns a dict:
        converged   : did the orbit settle onto a root?
        root_index  : index into the polynomial's roots, or -1 if it didn't
                      converge (e.g. it fell into a cycle)
        iterations  : steps taken
        zr, zi      : the final z
    """
    spec = POLYS[poly]
    coeffs = spec["coeffs"]
    dcoeffs = _deriv(coeffs)
    roots = spec["roots"]

    z = complex(zr, zi)
    n = 0
    converged = False
    while n < max_iter:
        dp = _polyval(dcoeffs, z)
        if abs(dp) < 1e-14:        # derivative ~ 0: the step blows up
            break
        step = a * _polyval(coeffs, z) / dp
        z -= step
        n += 1
        if abs(step) < tol:
            converged = True
            break

    root_index = -1
    if converged:
        best, bestd = -1, float("inf")
        for i, (rr, ri) in enumerate(roots):
            d = (z.real - rr) ** 2 + (z.imag - ri) ** 2
            if d < bestd:
                best, bestd = i, d
        root_index = best

    return {
        "converged": converged,
        "root_index": root_index,
        "iterations": n,
        "zr": z.real,
        "zi": z.imag,
    }


def orbit(zr, zi, poly="cubic", steps=20, a=1.0, tol=TOL):
    """The Newton iterates z(0..) from a start point, as (re, im) pairs.

    Stops once the step is tiny (converged) so the list can be shorter.
    """
    spec = POLYS[poly]
    coeffs = spec["coeffs"]
    dcoeffs = _deriv(coeffs)
    z = complex(zr, zi)
    pts = [(z.real, z.imag)]
    for _ in range(max(0, steps - 1)):
        dp = _polyval(dcoeffs, z)
        if abs(dp) < 1e-14:
            break
        step = a * _polyval(coeffs, z) / dp
        z -= step
        pts.append((z.real, z.imag))
        if abs(step) < tol:
            break
    return pts


def classify(zr, zi, poly="cubic", max_iter=DEFAULT_MAX_ITER, a=1.0, tol=TOL):
    """A friendly verdict for one starting point, for the inspector panel."""
    res = newton(zr, zi, poly, max_iter, tol, a)
    roots = POLYS[poly]["roots"]
    if not res["converged"]:
        verdict = "Never settles — caught in a cycle or creeping along a basin edge."
        root = None
    else:
        rr, ri = roots[res["root_index"]]
        sign = "+" if ri >= 0 else "-"
        root = f"{rr:.4f} {sign} {abs(ri):.4f}i"
        speed = ("snaps to" if res["iterations"] <= 6 else
                 "drifts to" if res["iterations"] < max_iter * 0.5 else
                 "crawls to")
        verdict = f"Converges — {speed} root #{res['root_index'] + 1} ({root})."
    res = dict(res)
    res["root"] = root
    res["root_label"] = POLYS[poly]["label"]
    res["max_iter"] = max_iter
    res["verdict"] = verdict
    return res


if __name__ == "__main__":
    # --- sanity checks -----------------------------------------------------
    # z^3 - 1: a start hugging the real root falls to root #0 = (1, 0).
    r = newton(1.3, 0.0, "cubic")
    assert r["converged"] and r["root_index"] == 0

    # A start near the upper complex root falls to root #1.
    r = newton(-0.5, 0.9, "cubic")
    assert r["converged"] and r["root_index"] == 1

    # The classic trap: z^3 - 2z + 2 sends z = 0 into a 0 -> 1 -> 0 cycle,
    # so it never converges.
    r = newton(0.0, 0.0, "tricky")
    assert not r["converged"] and r["root_index"] == -1

    # Every polynomial's cached roots really are roots (p(root) ~ 0).
    for name, spec in POLYS.items():
        for rr, ri in spec["roots"]:
            assert abs(_polyval(spec["coeffs"], complex(rr, ri))) < 1e-9, name

    # The orbit of a converging start ends right at its root.
    o = orbit(1.3, 0.0, "cubic")
    last = o[-1]
    assert abs(last[0] - 1.0) < 1e-3 and abs(last[1]) < 1e-3

    print("Newton fractal logic — all sanity checks passed.\n")

    # A tiny ASCII portrait of the z^3 - 1 basins (digit = which root).
    rows = []
    for iy in range(22):
        zi = 1.6 - iy * (3.2 / 21)
        line = []
        for ix in range(64):
            zr = -1.8 + ix * (3.6 / 63)
            res = newton(zr, zi, "cubic", 40)
            line.append(str(res["root_index"] + 1) if res["converged"] else ".")
        rows.append("".join(line))
    print("z^3 - 1 basins (1/2/3 = which root)\n")
    print("\n".join(rows))
