"""pH / acid-base calculator — pure-Python logic.

All concentrations are in mol/L. Calculations use Kw = 1.0e-14 (25 C).

The four pieces — pH, pOH, [H+], [OH-] — are tied by:
    pH  = -log10([H+])
    pOH = -log10([OH-])
    [H+] * [OH-] = Kw
    pH + pOH     = 14

Public helpers (each returns the same {pH, pOH, H, OH, classification} dict):
    from_ph(pH)          pH       -> all four
    from_poh(pOH)        pOH      -> all four
    from_h(h)            [H+]     -> all four
    from_oh(oh)          [OH-]    -> all four
    strong_acid(c)       strong monoprotic acid    (concentration -> pH)
    strong_base(c)       strong monohydroxide base (concentration -> pH)
    weak_acid(Ka, c)     weak monoprotic acid  (Ka, concentration -> pH)
    weak_base(Kb, c)     weak monoprotic base  (Kb, concentration -> pH)
"""

import math

KW = 1.0e-14


def _classify(pH):
    if pH < 7:
        return "Acidic"
    if pH > 7:
        return "Basic"
    return "Neutral"


def _result(h):
    if h <= 0:
        raise ValueError("[H+] must be positive")
    oh = KW / h
    pH = -math.log10(h)
    pOH = -math.log10(oh)
    pH_r = round(pH, 4)
    return {
        "pH": pH_r,
        "pOH": round(pOH, 4),
        "H": h,
        "OH": oh,
        "classification": _classify(pH_r),
    }


def from_ph(pH):
    return _result(10 ** (-pH))


def from_poh(pOH):
    oh = 10 ** (-pOH)
    return _result(KW / oh)


def from_h(h):
    return _result(h)


def from_oh(oh):
    if oh <= 0:
        raise ValueError("[OH-] must be positive")
    return _result(KW / oh)


def strong_acid(c):
    """Strong monoprotic acid at concentration c (mol/L).

    Includes water autoionization, which matters for very dilute solutions:
        [H+]^2 - c[H+] - Kw = 0
    """
    if c <= 0:
        raise ValueError("concentration must be positive")
    h = (c + math.sqrt(c * c + 4 * KW)) / 2
    return _result(h)


def strong_base(c):
    """Strong monohydroxide base at concentration c (mol/L)."""
    if c <= 0:
        raise ValueError("concentration must be positive")
    oh = (c + math.sqrt(c * c + 4 * KW)) / 2
    return _result(KW / oh)


def weak_acid(Ka, c):
    """Weak monoprotic acid HA <-> H+ + A-.

    Solves the equilibrium quadratic without the 'x << c' approximation:
        x^2 + Ka * x - Ka * c = 0
    where x = [H+] contributed by the acid. Water autoionization is
    neglected — fine when x >> sqrt(Kw) ~ 1e-7, which holds for any
    practical weak-acid problem.
    """
    if Ka <= 0 or c <= 0:
        raise ValueError("Ka and concentration must be positive")
    x = (-Ka + math.sqrt(Ka * Ka + 4 * Ka * c)) / 2
    return _result(x)


def weak_base(Kb, c):
    """Weak monoprotic base B + H2O <-> BH+ + OH-."""
    if Kb <= 0 or c <= 0:
        raise ValueError("Kb and concentration must be positive")
    x = (-Kb + math.sqrt(Kb * Kb + 4 * Kb * c)) / 2
    return _result(KW / x)


if __name__ == "__main__":
    cases = [
        ("from_ph(7.0)", from_ph, (7.0,)),
        ("from_ph(3.0)", from_ph, (3.0,)),
        ("from_poh(4.0)", from_poh, (4.0,)),
        ("from_h(1e-3)", from_h, (1e-3,)),
        ("from_oh(1e-5)", from_oh, (1e-5,)),
        ("strong_acid(0.01) HCl", strong_acid, (0.01,)),
        ("strong_acid(1e-8) very dilute", strong_acid, (1e-8,)),
        ("strong_base(0.001) NaOH", strong_base, (0.001,)),
        ("weak_acid(1.8e-5, 0.1) acetic", weak_acid, (1.8e-5, 0.1)),
        ("weak_base(1.8e-5, 0.1) ammonia", weak_base, (1.8e-5, 0.1)),
    ]
    for label, fn, args in cases:
        r = fn(*args)
        print(f"{label:36s} -> pH {r['pH']:7.4f}  pOH {r['pOH']:7.4f}  "
              f"[H+]={r['H']:.3e}  [OH-]={r['OH']:.3e}  {r['classification']}")
        assert abs(r["pH"] + r["pOH"] - 14) < 1e-3
        assert abs(r["H"] * r["OH"] - KW) / KW < 1e-6
    print("identities ok")

    for bad in (-1, 0):
        for fn in (from_h, from_oh, strong_acid, strong_base):
            try:
                fn(bad)
            except ValueError as e:
                print(f"{fn.__name__}({bad}): {e}")
        for fn in (weak_acid, weak_base):
            try:
                fn(bad, 0.1)
            except ValueError as e:
                print(f"{fn.__name__}({bad}, 0.1): {e}")
            try:
                fn(1e-5, bad)
            except ValueError as e:
                print(f"{fn.__name__}(1e-5, {bad}): {e}")
