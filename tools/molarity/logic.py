"""Molarity calculator — pure-Python logic.

Two relationships tie everything together:

    moles = mass / molar_mass            (n = m / M)
    molarity = moles / volume_in_litres  (c = n / V)

From those, this module solves the everyday solution-chemistry problems:

  * **molarity from mass** — dissolve m grams of something (molar mass M) in
    V litres, what's the concentration?
  * **mass to prepare** — how many grams to make V litres of a c-molar solution?
  * **the c = n/V triangle** — give any two of molarity / moles / volume, get
    the third.
  * **dilution** — C1·V1 = C2·V2, solve for the missing one (the "how much
    stock do I need" question).

It also parses a **chemical formula** (``NaCl``, ``H2O``, ``Ca(OH)2``,
``CuSO4·5H2O``) into a molar mass, so the molar-mass field accepts either a
number or a formula. Standard atomic weights are from IUPAC.

All volumes are converted to litres for the math; results are reported back in
the unit the user chose.
"""

import json

# Standard atomic weights (IUPAC). For elements with no stable isotope, a
# representative value of the longest-lived isotope is used — fine for the
# school-level work this tool is for.
ATOMIC_WEIGHTS = {
    "H": 1.008, "He": 4.0026, "Li": 6.94, "Be": 9.0122, "B": 10.81,
    "C": 12.011, "N": 14.007, "O": 15.999, "F": 18.998, "Ne": 20.180,
    "Na": 22.990, "Mg": 24.305, "Al": 26.982, "Si": 28.085, "P": 30.974,
    "S": 32.06, "Cl": 35.45, "Ar": 39.948, "K": 39.098, "Ca": 40.078,
    "Sc": 44.956, "Ti": 47.867, "V": 50.942, "Cr": 51.996, "Mn": 54.938,
    "Fe": 55.845, "Co": 58.933, "Ni": 58.693, "Cu": 63.546, "Zn": 65.38,
    "Ga": 69.723, "Ge": 72.630, "As": 74.922, "Se": 78.971, "Br": 79.904,
    "Kr": 83.798, "Rb": 85.468, "Sr": 87.62, "Y": 88.906, "Zr": 91.224,
    "Nb": 92.906, "Mo": 95.95, "Tc": 98.0, "Ru": 101.07, "Rh": 102.91,
    "Pd": 106.42, "Ag": 107.87, "Cd": 112.41, "In": 114.82, "Sn": 118.71,
    "Sb": 121.76, "Te": 127.60, "I": 126.90, "Xe": 131.29, "Cs": 132.91,
    "Ba": 137.33, "La": 138.91, "Ce": 140.12, "Pr": 140.91, "Nd": 144.24,
    "Pm": 145.0, "Sm": 150.36, "Eu": 151.96, "Gd": 157.25, "Tb": 158.93,
    "Dy": 162.50, "Ho": 164.93, "Er": 167.26, "Tm": 168.93, "Yb": 173.05,
    "Lu": 174.97, "Hf": 178.49, "Ta": 180.95, "W": 183.84, "Re": 186.21,
    "Os": 190.23, "Ir": 192.22, "Pt": 195.08, "Au": 196.97, "Hg": 200.59,
    "Tl": 204.38, "Pb": 207.2, "Bi": 208.98, "Po": 209.0, "At": 210.0,
    "Rn": 222.0, "Fr": 223.0, "Ra": 226.0, "Ac": 227.0, "Th": 232.04,
    "Pa": 231.04, "U": 238.03, "Np": 237.0, "Pu": 244.0, "Am": 243.0,
    "Cm": 247.0, "Bk": 247.0, "Cf": 251.0, "Es": 252.0, "Fm": 257.0,
    "Md": 258.0, "No": 259.0, "Lr": 262.0, "Rf": 267.0, "Db": 268.0,
    "Sg": 269.0, "Bh": 270.0, "Hs": 269.0, "Mt": 278.0, "Ds": 281.0,
    "Rg": 282.0, "Cn": 285.0, "Nh": 286.0, "Fl": 289.0, "Mc": 290.0,
    "Lv": 293.0, "Ts": 294.0, "Og": 294.0,
}

VOLUME_TO_L = {"L": 1.0, "mL": 1e-3, "µL": 1e-6, "uL": 1e-6}


def to_litres(value, unit):
    if unit not in VOLUME_TO_L:
        raise ValueError(f"Unknown volume unit '{unit}'")
    return value * VOLUME_TO_L[unit]


def from_litres(litres, unit):
    return litres / VOLUME_TO_L[unit]


# ── chemical formula → molar mass ────────────────────────────────────────────

def _parse_group(s):
    """Stack-based parse of a formula segment (handles nested parentheses)."""
    stack = [{}]
    i, n = 0, len(s)
    while i < n:
        ch = s[i]
        if ch == "(" or ch == "[":
            stack.append({})
            i += 1
        elif ch == ")" or ch == "]":
            i += 1
            j = i
            while j < n and s[j].isdigit():
                j += 1
            mult = int(s[i:j]) if j > i else 1
            i = j
            if len(stack) == 1:
                raise ValueError("Unbalanced parentheses")
            top = stack.pop()
            for el, c in top.items():
                stack[-1][el] = stack[-1].get(el, 0) + c * mult
        elif ch.isalpha():
            if not ch.isupper():
                raise ValueError(
                    f"'{ch}' — element symbols start with a capital letter")
            j = i + 1
            if j < n and s[j].islower():
                j += 1
            sym = s[i:j]
            i = j
            k = i
            while k < n and s[k].isdigit():
                k += 1
            cnt = int(s[i:k]) if k > i else 1
            i = k
            if sym not in ATOMIC_WEIGHTS:
                raise ValueError(f"Unknown element '{sym}'")
            stack[-1][sym] = stack[-1].get(sym, 0) + cnt
        elif ch.isspace():
            i += 1
        else:
            raise ValueError(f"Unexpected character '{ch}' in formula")
    if len(stack) != 1:
        raise ValueError("Unbalanced parentheses")
    return stack[0]


def parse_formula(formula):
    """Parse a formula into ``{element: count}``.

    Supports parentheses/brackets, subscripts, and hydrates written with a
    middot, period, or asterisk plus a leading coefficient (``CuSO4·5H2O``).
    """
    f = (formula or "").strip()
    if not f:
        raise ValueError("Enter a chemical formula")

    counts = {}
    for raw_seg in f.replace("·", "*").replace(".", "*").split("*"):
        seg = raw_seg.strip()
        if not seg:
            continue
        coeff = 1
        d = 0
        while d < len(seg) and seg[d].isdigit():
            d += 1
        if d:
            coeff = int(seg[:d])
            seg = seg[d:]
        for el, c in _parse_group(seg).items():
            counts[el] = counts.get(el, 0) + c * coeff
    if not counts:
        raise ValueError("No elements found in formula")
    return counts


def molar_mass(formula):
    """Molar mass (g/mol) of a formula, with a per-element breakdown."""
    counts = parse_formula(formula)
    breakdown, total = [], 0.0
    for el, cnt in counts.items():
        w = ATOMIC_WEIGHTS[el]
        sub = w * cnt
        total += sub
        breakdown.append({"element": el, "count": cnt,
                          "weight": w, "subtotal": round(sub, 4)})
    return {"formula": formula.strip(),
            "molar_mass": round(total, 4),
            "breakdown": breakdown}


def resolve_molar_mass(text):
    """Accept either a number or a chemical formula.

    Returns ``(grams_per_mole, formula_info_or_None)``.
    """
    t = str(text).strip()
    if not t:
        raise ValueError("Enter a molar mass or chemical formula")
    try:
        v = float(t)
    except ValueError:
        info = molar_mass(t)
        return info["molar_mass"], info
    if v <= 0:
        raise ValueError("Molar mass must be positive")
    return v, None


# ── the core relationships ───────────────────────────────────────────────────

def _pos(name, value):
    if value is None:
        raise ValueError(f"{name} is required")
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def _opt(value):
    """A form value that may be blank → None, else float."""
    if value is None:
        return None
    s = str(value).strip()
    if s == "":
        return None
    return float(s)


def molarity_from_mass(mass_g, molar_mass_g, volume_l):
    _pos("Mass", mass_g)
    _pos("Molar mass", molar_mass_g)
    _pos("Volume", volume_l)
    moles = mass_g / molar_mass_g
    return {"molarity": moles / volume_l, "moles": moles}


def mass_to_prepare(molarity, volume_l, molar_mass_g):
    _pos("Molarity", molarity)
    _pos("Volume", volume_l)
    _pos("Molar mass", molar_mass_g)
    moles = molarity * volume_l
    return {"moles": moles, "mass": moles * molar_mass_g}


def solve_cnv(molarity=None, moles=None, volume_l=None):
    """Solve c = n/V for whichever of the three is missing (exactly one)."""
    missing = [k for k, v in
               (("molarity", molarity), ("moles", moles), ("volume", volume_l))
               if v is None]
    if len(missing) != 1:
        raise ValueError("Leave exactly one of molarity / moles / volume blank")
    if molarity is None:
        _pos("Moles", moles); _pos("Volume", volume_l)
        molarity = moles / volume_l
    elif moles is None:
        _pos("Molarity", molarity); _pos("Volume", volume_l)
        moles = molarity * volume_l
    else:
        _pos("Molarity", molarity); _pos("Moles", moles)
        volume_l = moles / molarity
    return {"molarity": molarity, "moles": moles, "volume_l": volume_l,
            "solved": missing[0]}


def solve_dilution(c1=None, v1=None, c2=None, v2=None):
    """Solve C1·V1 = C2·V2 for the one missing value (volumes already in L)."""
    missing = [k for k, v in
               (("c1", c1), ("v1", v1), ("c2", c2), ("v2", v2)) if v is None]
    if len(missing) != 1:
        raise ValueError("Leave exactly one field blank to solve for it")
    if c1 is None:
        _pos("V1", v1); _pos("C2", c2); _pos("V2", v2)
        c1 = c2 * v2 / v1
    elif v1 is None:
        _pos("C1", c1); _pos("C2", c2); _pos("V2", v2)
        v1 = c2 * v2 / c1
        if v1 > v2:
            raise ValueError(
                "Stock is more dilute than the target — you can't reach C2 by "
                "dilution")
    elif c2 is None:
        _pos("C1", c1); _pos("V1", v1); _pos("V2", v2)
        c2 = c1 * v1 / v2
    else:
        _pos("C1", c1); _pos("V1", v1); _pos("C2", c2)
        v2 = c1 * v1 / c2
    return {"c1": c1, "v1": v1, "c2": c2, "v2": v2, "solved": missing[0]}


# ── UI orchestration ─────────────────────────────────────────────────────────

def solve(mode, payload):
    """Dispatch a form ``payload`` (dict of strings) for the given mode.

    Returns a display-ready dict: a headline ``result`` plus ``details`` rows
    and an optional molar-mass ``breakdown``.
    """
    if mode == "molar-mass":
        info = molar_mass(payload["formula"])
        return {
            "result": {"label": f"Molar mass of {info['formula']}",
                       "value": info["molar_mass"], "unit": "g/mol"},
            "details": [],
            "breakdown": info["breakdown"],
        }

    if mode == "mass-to-molarity":
        mass = _pos("Mass", _opt(payload["mass"]))
        mm, info = resolve_molar_mass(payload["molar_mass"])
        vol = to_litres(_pos("Volume", _opt(payload["volume"])),
                        payload["volume_unit"])
        r = molarity_from_mass(mass, mm, vol)
        return {
            "result": {"label": "Molarity", "value": r["molarity"], "unit": "mol/L"},
            "details": [
                {"label": "Moles of solute", "value": r["moles"], "unit": "mol"},
                {"label": "Molar mass used", "value": mm, "unit": "g/mol"},
                {"label": "Volume", "value": vol, "unit": "L"},
            ],
            "breakdown": info["breakdown"] if info else None,
        }

    if mode == "molarity-to-mass":
        molc = _pos("Molarity", _opt(payload["molarity"]))
        mm, info = resolve_molar_mass(payload["molar_mass"])
        vol = to_litres(_pos("Volume", _opt(payload["volume"])),
                        payload["volume_unit"])
        r = mass_to_prepare(molc, vol, mm)
        return {
            "result": {"label": "Mass to weigh out", "value": r["mass"], "unit": "g"},
            "details": [
                {"label": "Moles needed", "value": r["moles"], "unit": "mol"},
                {"label": "Molar mass used", "value": mm, "unit": "g/mol"},
                {"label": "Target", "value": molc, "unit": "mol/L"},
            ],
            "breakdown": info["breakdown"] if info else None,
        }

    if mode == "cnv":
        vol_in = _opt(payload["volume"])
        vol_l = to_litres(vol_in, payload["volume_unit"]) if vol_in is not None else None
        r = solve_cnv(_opt(payload["molarity"]), _opt(payload["moles"]), vol_l)
        vol_unit = payload["volume_unit"]
        labels = {"molarity": "Molarity", "moles": "Moles", "volume": "Volume"}
        units = {"molarity": "mol/L", "moles": "mol", "volume": vol_unit}
        values = {"molarity": r["molarity"], "moles": r["moles"],
                  "volume": from_litres(r["volume_l"], vol_unit)}
        solved = r["solved"]
        details = [{"label": labels[k], "value": values[k], "unit": units[k]}
                   for k in ("molarity", "moles", "volume") if k != solved]
        return {
            "result": {"label": labels[solved], "value": values[solved],
                       "unit": units[solved]},
            "details": details,
            "breakdown": None,
        }

    if mode == "dilution":
        v1_in, v2_in = _opt(payload["v1"]), _opt(payload["v2"])
        u1, u2 = payload["v1_unit"], payload["v2_unit"]
        v1_l = to_litres(v1_in, u1) if v1_in is not None else None
        v2_l = to_litres(v2_in, u2) if v2_in is not None else None
        r = solve_dilution(_opt(payload["c1"]), v1_l, _opt(payload["c2"]), v2_l)
        solved = r["solved"]
        # report each volume in its own unit
        vals = {"c1": r["c1"], "v1": from_litres(r["v1"], u1),
                "c2": r["c2"], "v2": from_litres(r["v2"], u2)}
        labels = {"c1": "Stock concentration (C1)", "v1": "Stock volume (V1)",
                  "c2": "Final concentration (C2)", "v2": "Final volume (V2)"}
        units = {"c1": "mol/L", "v1": u1, "c2": "mol/L", "v2": u2}
        details = [{"label": labels[k], "value": vals[k], "unit": units[k]}
                   for k in ("c1", "v1", "c2", "v2") if k != solved]
        out = {
            "result": {"label": labels[solved], "value": vals[solved],
                       "unit": units[solved]},
            "details": details,
            "breakdown": None,
        }
        # When we solved the stock volume, the rest is solvent to add.
        if solved == "v1":
            diluent_l = r["v2"] - r["v1"]
            out["note"] = (f"Add {round(from_litres(diluent_l, u2), 4):g} {u2} "
                           f"of solvent to the stock to reach {vals['v2']:g} {u2}.")
        return out

    raise ValueError(f"Unknown mode '{mode}'")


def solve_json(mode, payload_json):
    return json.dumps(solve(mode, json.loads(payload_json)))


def molar_mass_json(formula):
    return json.dumps(molar_mass(formula))


if __name__ == "__main__":
    # ── formula parsing / molar mass ──
    assert abs(molar_mass("H2O")["molar_mass"] - 18.015) < 0.01
    assert abs(molar_mass("NaCl")["molar_mass"] - 58.44) < 0.01
    assert abs(molar_mass("C6H12O6")["molar_mass"] - 180.156) < 0.01
    assert abs(molar_mass("Ca(OH)2")["molar_mass"] - 74.092) < 0.01
    assert abs(molar_mass("(NH4)2SO4")["molar_mass"] - 132.14) < 0.02
    assert abs(molar_mass("CuSO4·5H2O")["molar_mass"] - 249.68) < 0.05
    assert abs(molar_mass("KAl(SO4)2·12H2O")["molar_mass"] - 474.38) < 0.1
    print("molar masses:",
          {f: molar_mass(f)["molar_mass"]
           for f in ("H2O", "NaCl", "C6H12O6", "Ca(OH)2", "CuSO4·5H2O")})

    mm, info = resolve_molar_mass("58.44")
    assert mm == 58.44 and info is None
    mm, info = resolve_molar_mass("NaCl")
    assert info is not None and abs(mm - 58.44) < 0.01

    # ── core relationships ──
    # 1 mol NaCl (58.44 g) in 0.5 L → 2 M
    r = molarity_from_mass(58.44, 58.44, 0.5)
    assert abs(r["molarity"] - 2.0) < 1e-9 and abs(r["moles"] - 1.0) < 1e-9

    # make 0.25 L of 0.1 M NaCl → 0.025 mol → 1.461 g
    r = mass_to_prepare(0.1, 0.25, 58.44)
    assert abs(r["moles"] - 0.025) < 1e-9 and abs(r["mass"] - 1.461) < 1e-3

    # c = n/V triangle
    assert abs(solve_cnv(moles=0.5, volume_l=2.0)["molarity"] - 0.25) < 1e-9
    assert abs(solve_cnv(molarity=0.25, volume_l=2.0)["moles"] - 0.5) < 1e-9
    assert abs(solve_cnv(molarity=0.25, moles=0.5)["volume_l"] - 2.0) < 1e-9

    # dilution: 1 M stock to make 0.5 L of 0.1 M → need 0.05 L stock
    d = solve_dilution(c1=1.0, c2=0.1, v2=0.5)
    assert abs(d["v1"] - 0.05) < 1e-9, d

    # ── unit helpers ──
    assert to_litres(250, "mL") == 0.25
    assert abs(from_litres(0.25, "mL") - 250) < 1e-9

    # ── orchestration (the JSON path the browser uses) ──
    out = json.loads(solve_json("mass-to-molarity", json.dumps(
        {"mass": "58.44", "molar_mass": "NaCl", "volume": "500", "volume_unit": "mL"})))
    assert abs(out["result"]["value"] - 2.0) < 1e-6
    assert out["breakdown"] is not None
    print("mass→molarity:", out["result"])

    out = json.loads(solve_json("molarity-to-mass", json.dumps(
        {"molarity": "0.1", "molar_mass": "NaCl", "volume": "250", "volume_unit": "mL"})))
    assert abs(out["result"]["value"] - 1.461) < 1e-3
    print("molarity→mass:", out["result"])

    out = json.loads(solve_json("cnv", json.dumps(
        {"molarity": "", "moles": "0.5", "volume": "2", "volume_unit": "L"})))
    assert out["result"]["label"] == "Molarity"
    assert abs(out["result"]["value"] - 0.25) < 1e-6

    out = json.loads(solve_json("dilution", json.dumps(
        {"c1": "1", "v1": "", "c2": "0.1", "v2": "500",
         "v1_unit": "mL", "v2_unit": "mL"})))
    assert abs(out["result"]["value"] - 50) < 1e-6  # 50 mL stock
    assert "note" in out
    print("dilution:", out["result"], "|", out["note"])

    # ── errors ──
    bad_cases = [
        ("molar-mass", {"formula": "Xx2"}),
        ("molar-mass", {"formula": "H(2O"}),
        ("mass-to-molarity", {"mass": "-1", "molar_mass": "NaCl",
                              "volume": "1", "volume_unit": "L"}),
        ("cnv", {"molarity": "", "moles": "", "volume": "1", "volume_unit": "L"}),
        ("dilution", {"c1": "0.1", "v1": "", "c2": "1", "v2": "500",
                      "v1_unit": "mL", "v2_unit": "mL"}),  # can't concentrate
    ]
    for mode, payload in bad_cases:
        try:
            solve(mode, payload)
            raise AssertionError(f"expected failure for {mode} {payload}")
        except ValueError as e:
            print(f"{mode:18s} -> {e}")

    print("all checks passed")
