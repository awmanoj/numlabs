"""Golden ratio (phi) — pure-Python logic.

The golden ratio phi = (1 + sqrt(5)) / 2 = 1.6180339887... is the positive
solution of x^2 = x + 1, equivalently x = 1 + 1/x. It satisfies the tidy
identities phi^2 = phi + 1 and 1/phi = phi - 1, so 1/phi = 0.6180339887...

This module covers the calculators the page exposes:

- counterpart(n)     : the larger (n*phi) and smaller (n/phi) golden partners
                       of a number, plus the golden cut of n into two parts.
- compare(a, b)      : how close the ratio of two numbers is to phi.
- rectangle(width)   : the golden height for a width (both orientations),
                       with area and diagonal.
- body_check(h, nav) : how close height : navel-to-floor is to phi.
- fibonacci_ratios(k): successive Fibonacci ratios converging on phi.
- phi_digits(places) : phi to `places` decimal places, via integer sqrt.

Everything except phi_digits works in ordinary floats; phi_digits uses
math.isqrt so the digits are exact to the requested precision.
"""

import math

PHI = (1 + 5 ** 0.5) / 2          # 1.61803398874989...
INV_PHI = PHI - 1                  # 1/phi = 0.61803398874989...


def _verdict(pct_error):
    """Closeness band for a percentage error away from phi."""
    e = abs(pct_error)
    if e < 0.5:
        return "Spot on — that's golden."
    if e < 2:
        return "Very close to golden."
    if e < 5:
        return "In the golden ballpark."
    return "Not particularly golden."


def counterpart(n):
    """Golden partners of n.

    larger  = n * phi   (n is the short part of a golden pair)
    smaller = n / phi   (n is the long part of a golden pair)

    Also splits n itself into a golden cut: a long part and a short part
    whose lengths are in the ratio phi : 1 and which sum back to n. The long
    part is n/phi and the short part is n/phi^2 = n - n/phi.
    """
    n = float(n)
    larger = n * PHI
    smaller = n / PHI
    long_part = n / PHI
    short_part = n - long_part
    return {
        "n": n,
        "phi": PHI,
        "larger": larger,
        "smaller": smaller,
        "long_part": long_part,
        "short_part": short_part,
    }


def compare(a, b):
    """Compare the ratio of two positive numbers against phi."""
    a, b = float(a), float(b)
    if a <= 0 or b <= 0:
        raise ValueError("Both numbers must be positive.")
    hi, lo = (a, b) if a >= b else (b, a)
    ratio = hi / lo
    pct_error = (ratio - PHI) / PHI * 100
    return {
        "a": a,
        "b": b,
        "ratio": ratio,
        "phi": PHI,
        "difference": ratio - PHI,
        "pct_error": pct_error,
        "verdict": _verdict(pct_error),
    }


def rectangle(width):
    """Golden rectangle dimensions from a width.

    A golden rectangle has its long side and short side in the ratio phi : 1.
    There are two readings of a given width:

    - width is the LONG side  -> height = width / phi   (landscape)
    - width is the SHORT side -> height = width * phi   (portrait)

    The portrait reading is reported as the primary "golden height" because
    "enter width, get the height that makes it golden" most naturally means
    the taller, more striking rectangle; the landscape reading is also
    returned. Each comes with its area and diagonal.
    """
    width = float(width)
    if width <= 0:
        raise ValueError("Width must be positive.")

    tall = width * PHI       # width is the short side
    short = width / PHI      # width is the long side

    def rect(w, h):
        return {
            "width": w,
            "height": h,
            "area": w * h,
            "diagonal": math.hypot(w, h),
        }

    return {
        "phi": PHI,
        "width": width,
        "tall": rect(width, tall),    # height = width * phi
        "wide": rect(width, short),   # height = width / phi
    }


def body_check(height, navel_to_floor):
    """How close height : navel-to-floor sits to phi.

    A long-standing "golden body" claim: total height divided by the height
    of the navel from the floor lands near phi. Measure in the same units;
    only the ratio matters.
    """
    height = float(height)
    navel_to_floor = float(navel_to_floor)
    if height <= 0 or navel_to_floor <= 0:
        raise ValueError("Both measurements must be positive.")
    if navel_to_floor >= height:
        raise ValueError("Navel-to-floor must be less than total height.")
    ratio = height / navel_to_floor
    pct_error = (ratio - PHI) / PHI * 100
    # The navel height that would make the ratio exactly phi.
    ideal_navel = height / PHI
    return {
        "height": height,
        "navel_to_floor": navel_to_floor,
        "ratio": ratio,
        "phi": PHI,
        "pct_error": pct_error,
        "ideal_navel": ideal_navel,
        "verdict": _verdict(pct_error),
    }


def fibonacci_ratios(count):
    """Successive Fibonacci ratios F(n+1)/F(n), converging to phi.

    Returns `count` rows starting from 1/1. The ratio overshoots and
    undershoots phi alternately, the error shrinking by a factor of ~phi^2
    each step, so by a dozen terms it agrees with phi to several decimals.
    """
    count = int(count)
    if count < 1:
        raise ValueError("count must be >= 1")
    if count > 90:
        raise ValueError("count must be <= 90 (float ratios stay exact here)")

    fibs = [1, 1]
    while len(fibs) < count + 1:
        fibs.append(fibs[-1] + fibs[-2])

    rows = []
    for i in range(count):
        a, b = fibs[i], fibs[i + 1]
        ratio = b / a
        rows.append({
            "a": a,
            "b": b,
            "ratio": ratio,
            "error": ratio - PHI,
        })
    return rows


def phi_digits(places):
    """phi to `places` decimal places as the string '1.618...'.

    Computes floor(sqrt(5) * 10^p) with math.isqrt for p = places + guard
    digits, forms phi*10^p = (10^p + sqrt5_scaled) // 2, then trims the guard
    digits. isqrt is exact, so every returned digit is correct (the result is
    truncated, not rounded, at the last place).
    """
    places = int(places)
    if places < 0:
        raise ValueError("places must be >= 0")
    if places > 2000:
        raise ValueError("places must be <= 2000")

    guard = 10
    p = places + guard
    sqrt5_scaled = math.isqrt(5 * 10 ** (2 * p))   # floor(sqrt(5) * 10^p)
    phi_scaled = (10 ** p + sqrt5_scaled) // 2      # floor(phi * 10^p)

    s = str(phi_scaled)                             # length p + 1 (int part '1')
    int_part = s[:-p]
    frac = s[-p:][:places]
    digits = int_part if places == 0 else f"{int_part}.{frac}"
    return {"places": places, "digits": digits}


if __name__ == "__main__":
    print(f"phi = {PHI!r}, 1/phi = {INV_PHI!r}")

    c = counterpart(100)
    print(f"\ncounterpart(100): larger={c['larger']:.4f} smaller={c['smaller']:.4f} "
          f"cut={c['long_part']:.4f}+{c['short_part']:.4f}")
    assert abs(c["larger"] - 161.803398875) < 1e-6
    assert abs(c["smaller"] - 61.803398875) < 1e-6
    assert abs(c["long_part"] + c["short_part"] - 100) < 1e-9

    cm = compare(16, 9)
    print(f"compare(16,9): ratio={cm['ratio']:.5f} err={cm['pct_error']:.2f}% -> {cm['verdict']}")
    cm2 = compare(89, 55)
    print(f"compare(89,55): ratio={cm2['ratio']:.5f} err={cm2['pct_error']:.3f}% -> {cm2['verdict']}")
    assert abs(cm2["pct_error"]) < 0.5

    r = rectangle(100)
    print(f"rectangle(100): tall h={r['tall']['height']:.4f} wide h={r['wide']['height']:.4f}")
    assert abs(r["tall"]["height"] - 161.803398875) < 1e-6
    assert abs(r["wide"]["height"] - 61.803398875) < 1e-6
    # both are golden: long/short == phi
    assert abs(r["tall"]["height"] / r["tall"]["width"] - PHI) < 1e-9
    assert abs(r["wide"]["width"] / r["wide"]["height"] - PHI) < 1e-9

    b = body_check(180, 111.25)
    print(f"body_check(180,111.25): ratio={b['ratio']:.4f} err={b['pct_error']:.3f}% "
          f"ideal navel={b['ideal_navel']:.2f} -> {b['verdict']}")

    print("\nFibonacci ratios:")
    for row in fibonacci_ratios(12):
        print(f"  {row['b']:>3}/{row['a']:<3} = {row['ratio']:.8f}  (err {row['error']:+.2e})")
    last = fibonacci_ratios(20)[-1]
    assert abs(last["error"]) < 1e-7

    d = phi_digits(50)
    print(f"\nphi to 50 dp: {d['digits']}")
    assert d["digits"].startswith("1.6180339887498948482045868343656381177203091798057")
    assert len(phi_digits(1000)["digits"]) == 1002  # '1.' + 1000 digits
    assert phi_digits(0)["digits"] == "1"

    # error cases
    for fn, args in [(compare, (0, 5)), (rectangle, (-1,)), (body_check, (170, 200)),
                     (phi_digits, (3000,)), (fibonacci_ratios, (0,))]:
        try:
            fn(*args)
            print(f"!! {fn.__name__}{args} did not raise")
        except ValueError as e:
            print(f"{fn.__name__}{args}: {e}")

    print("\nall sanity checks passed")
