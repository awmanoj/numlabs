"""Color converter — pure-Python logic.

Parses a CSS color in any common form and converts it between formats:

  * **HEX** — ``#rgb``, ``#rgba``, ``#rrggbb``, ``#rrggbbaa``
  * **RGB** — ``rgb(255, 0, 0)`` / ``rgba(255,0,0,.5)`` / ``rgb(255 0 0 / 50%)``
  * **HSL** — ``hsl(120, 50%, 50%)`` / ``hsla(...)``
  * **named** — the 148 CSS color keywords (``tomato``, ``rebeccapurple``, …)

and derives **HSV/HSB** and **CMYK** for design tools.

It also does the accessibility job a color picker can't: WCAG **contrast
ratio** between a foreground and background color, with AA / AAA pass-fail
verdicts for normal and large text — the reason this is a developer tool, not
just a novelty.

All channels are kept as ``r, g, b`` integers (0–255) plus an alpha float
(0–1) internally; everything else is derived on demand.
"""

import re

# The 148 CSS3 / CSS Color Module named colors. Lets people paste "tomato"
# or "rebeccapurple" and get the hex back.
NAMED = {
    "aliceblue": "f0f8ff", "antiquewhite": "faebd7", "aqua": "00ffff",
    "aquamarine": "7fffd4", "azure": "f0ffff", "beige": "f5f5dc",
    "bisque": "ffe4c4", "black": "000000", "blanchedalmond": "ffebcd",
    "blue": "0000ff", "blueviolet": "8a2be2", "brown": "a52a2a",
    "burlywood": "deb887", "cadetblue": "5f9ea0", "chartreuse": "7fff00",
    "chocolate": "d2691e", "coral": "ff7f50", "cornflowerblue": "6495ed",
    "cornsilk": "fff8dc", "crimson": "dc143c", "cyan": "00ffff",
    "darkblue": "00008b", "darkcyan": "008b8b", "darkgoldenrod": "b8860b",
    "darkgray": "a9a9a9", "darkgreen": "006400", "darkgrey": "a9a9a9",
    "darkkhaki": "bdb76b", "darkmagenta": "8b008b", "darkolivegreen": "556b2f",
    "darkorange": "ff8c00", "darkorchid": "9932cc", "darkred": "8b0000",
    "darksalmon": "e9967a", "darkseagreen": "8fbc8f", "darkslateblue": "483d8b",
    "darkslategray": "2f4f4f", "darkslategrey": "2f4f4f", "darkturquoise": "00ced1",
    "darkviolet": "9400d3", "deeppink": "ff1493", "deepskyblue": "00bfff",
    "dimgray": "696969", "dimgrey": "696969", "dodgerblue": "1e90ff",
    "firebrick": "b22222", "floralwhite": "fffaf0", "forestgreen": "228b22",
    "fuchsia": "ff00ff", "gainsboro": "dcdcdc", "ghostwhite": "f8f8ff",
    "gold": "ffd700", "goldenrod": "daa520", "gray": "808080", "green": "008000",
    "greenyellow": "adff2f", "grey": "808080", "honeydew": "f0fff0",
    "hotpink": "ff69b4", "indianred": "cd5c5c", "indigo": "4b0082",
    "ivory": "fffff0", "khaki": "f0e68c", "lavender": "e6e6fa",
    "lavenderblush": "fff0f5", "lawngreen": "7cfc00", "lemonchiffon": "fffacd",
    "lightblue": "add8e6", "lightcoral": "f08080", "lightcyan": "e0ffff",
    "lightgoldenrodyellow": "fafad2", "lightgray": "d3d3d3", "lightgreen": "90ee90",
    "lightgrey": "d3d3d3", "lightpink": "ffb6c1", "lightsalmon": "ffa07a",
    "lightseagreen": "20b2aa", "lightskyblue": "87cefa", "lightslategray": "778899",
    "lightslategrey": "778899", "lightsteelblue": "b0c4de", "lightyellow": "ffffe0",
    "lime": "00ff00", "limegreen": "32cd32", "linen": "faf0e6", "magenta": "ff00ff",
    "maroon": "800000", "mediumaquamarine": "66cdaa", "mediumblue": "0000cd",
    "mediumorchid": "ba55d3", "mediumpurple": "9370db", "mediumseagreen": "3cb371",
    "mediumslateblue": "7b68ee", "mediumspringgreen": "00fa9a",
    "mediumturquoise": "48d1cc", "mediumvioletred": "c71585", "midnightblue": "191970",
    "mintcream": "f5fffa", "mistyrose": "ffe4e1", "moccasin": "ffe4b5",
    "navajowhite": "ffdead", "navy": "000080", "oldlace": "fdf5e6",
    "olive": "808000", "olivedrab": "6b8e23", "orange": "ffa500",
    "orangered": "ff4500", "orchid": "da70d6", "palegoldenrod": "eee8aa",
    "palegreen": "98fb98", "paleturquoise": "afeeee", "palevioletred": "db7093",
    "papayawhip": "ffefd5", "peachpuff": "ffdab9", "peru": "cd853f",
    "pink": "ffc0cb", "plum": "dda0dd", "powderblue": "b0e0e6", "purple": "800080",
    "rebeccapurple": "663399", "red": "ff0000", "rosybrown": "bc8f8f",
    "royalblue": "4169e1", "saddlebrown": "8b4513", "salmon": "fa8072",
    "sandybrown": "f4a460", "seagreen": "2e8b57", "seashell": "fff5ee",
    "sienna": "a0522d", "silver": "c0c0c0", "skyblue": "87ceeb",
    "slateblue": "6a5acd", "slategray": "708090", "slategrey": "708090",
    "snow": "fffafa", "springgreen": "00ff7f", "steelblue": "4682b4",
    "tan": "d2b48c", "teal": "008080", "thistle": "d8bfd8", "tomato": "ff6347",
    "turquoise": "40e0d0", "violet": "ee82ee", "wheat": "f5deb3", "white": "ffffff",
    "whitesmoke": "f5f5f5", "yellow": "ffff00", "yellowgreen": "9acd32",
}
# Reverse lookup (first name wins, so "aqua" not "cyan" for 00ffff, etc.).
_HEX_TO_NAME = {}
for _name, _hex in NAMED.items():
    _HEX_TO_NAME.setdefault(_hex, _name)


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _num(token):
    """Parse a number that may be a percentage; '%' returns 0–1 scale flag."""
    token = token.strip()
    if token.endswith("%"):
        return float(token[:-1]), True
    return float(token), False


def parse_color(text):
    """Parse a CSS color string into ``(r, g, b, a)``.

    ``r, g, b`` are ints 0–255; ``a`` is a float 0–1. Raises ValueError with a
    friendly message on anything it can't recognize.
    """
    s = text.strip().lower()
    if not s:
        raise ValueError("Enter a color")

    # Named color
    if s in NAMED:
        s = "#" + NAMED[s]

    # Hex
    if s.startswith("#"):
        h = s[1:]
        if not re.fullmatch(r"[0-9a-f]+", h or ""):
            raise ValueError(f"'{text.strip()}' has non-hex characters")
        if len(h) == 3:
            r, g, b = (int(c * 2, 16) for c in h)
            return r, g, b, 1.0
        if len(h) == 4:
            r, g, b, a = (int(c * 2, 16) for c in h)
            return r, g, b, round(a / 255, 4)
        if len(h) == 6:
            return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 1.0
        if len(h) == 8:
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16),
                    round(int(h[6:8], 16) / 255, 4))
        raise ValueError("Hex must be 3, 4, 6, or 8 digits")

    # Functional rgb()/rgba()/hsl()/hsla() — commas or spaces, optional "/ alpha"
    m = re.fullmatch(r"(rgba?|hsla?)\((.*)\)", s)
    if not m:
        raise ValueError(f"'{text.strip()}' is not a recognized color")
    fn, inner = m.group(1), m.group(2)
    inner = inner.replace("/", " ")
    parts = [p for p in re.split(r"[,\s]+", inner.strip()) if p]
    if len(parts) not in (3, 4):
        raise ValueError(f"{fn}() needs 3 values (plus optional alpha)")

    alpha = 1.0
    if len(parts) == 4:
        av, pct = _num(parts[3])
        alpha = _clamp(av / 100 if pct else av, 0.0, 1.0)

    if fn.startswith("rgb"):
        rgb = []
        for p in parts[:3]:
            v, pct = _num(p)
            rgb.append(int(round(v * 255 / 100)) if pct else int(round(v)))
        r, g, b = (_clamp(c, 0, 255) for c in rgb)
        return r, g, b, round(alpha, 4)

    # hsl
    h = _num(parts[0])[0] % 360
    sv = _clamp(_num(parts[1])[0], 0, 100)
    lv = _clamp(_num(parts[2])[0], 0, 100)
    r, g, b = hsl_to_rgb(h, sv, lv)
    return r, g, b, round(alpha, 4)


def rgb_to_hsl(r, g, b):
    """RGB (0–255) → HSL with h in 0–360, s/l in 0–100."""
    rf, gf, bf = r / 255, g / 255, b / 255
    mx, mn = max(rf, gf, bf), min(rf, gf, bf)
    d = mx - mn
    l = (mx + mn) / 2
    if d == 0:
        h = s = 0.0
    else:
        s = d / (1 - abs(2 * l - 1))
        if mx == rf:
            h = ((gf - bf) / d) % 6
        elif mx == gf:
            h = (bf - rf) / d + 2
        else:
            h = (rf - gf) / d + 4
        h *= 60
    return round(h, 1) % 360, round(s * 100, 1), round(l * 100, 1)


def hsl_to_rgb(h, s, l):
    """HSL (h 0–360, s/l 0–100) → RGB ints 0–255."""
    h = h % 360
    s, l = s / 100, l / 100
    c = (1 - abs(2 * l - 1)) * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = l - c / 2
    if h < 60:
        rp, gp, bp = c, x, 0
    elif h < 120:
        rp, gp, bp = x, c, 0
    elif h < 180:
        rp, gp, bp = 0, c, x
    elif h < 240:
        rp, gp, bp = 0, x, c
    elif h < 300:
        rp, gp, bp = x, 0, c
    else:
        rp, gp, bp = c, 0, x
    return (int(round((rp + m) * 255)),
            int(round((gp + m) * 255)),
            int(round((bp + m) * 255)))


def rgb_to_hsv(r, g, b):
    """RGB (0–255) → HSV/HSB with h 0–360, s/v 0–100."""
    rf, gf, bf = r / 255, g / 255, b / 255
    mx, mn = max(rf, gf, bf), min(rf, gf, bf)
    d = mx - mn
    if d == 0:
        h = 0.0
    elif mx == rf:
        h = (((gf - bf) / d) % 6) * 60
    elif mx == gf:
        h = ((bf - rf) / d + 2) * 60
    else:
        h = ((rf - gf) / d + 4) * 60
    s = 0.0 if mx == 0 else d / mx
    return round(h, 1) % 360, round(s * 100, 1), round(mx * 100, 1)


def rgb_to_cmyk(r, g, b):
    """RGB (0–255) → CMYK percentages (0–100)."""
    if r == g == b == 0:
        return 0.0, 0.0, 0.0, 100.0
    rf, gf, bf = r / 255, g / 255, b / 255
    k = 1 - max(rf, gf, bf)
    c = (1 - rf - k) / (1 - k)
    m = (1 - gf - k) / (1 - k)
    y = (1 - bf - k) / (1 - k)
    return (round(c * 100, 1), round(m * 100, 1),
            round(y * 100, 1), round(k * 100, 1))


def to_hex(r, g, b, a=1.0):
    """RGB(+alpha) → ``#rrggbb`` or ``#rrggbbaa`` when alpha < 1."""
    base = f"#{r:02x}{g:02x}{b:02x}"
    if a < 1:
        return base + f"{int(round(a * 255)):02x}"
    return base


def relative_luminance(r, g, b):
    """WCAG relative luminance of an sRGB color (0 = black, 1 = white)."""
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast_ratio(c1, c2):
    """WCAG contrast ratio (1–21) between two ``(r,g,b,...)`` colors."""
    l1 = relative_luminance(c1[0], c1[1], c1[2])
    l2 = relative_luminance(c2[0], c2[1], c2[2])
    hi, lo = max(l1, l2), min(l1, l2)
    return round((hi + 0.05) / (lo + 0.05), 2)


def wcag_levels(ratio):
    """Pass/fail verdicts for the four WCAG text thresholds."""
    return {
        "aa_normal": ratio >= 4.5,
        "aa_large": ratio >= 3.0,
        "aaa_normal": ratio >= 7.0,
        "aaa_large": ratio >= 4.5,
    }


def convert(text):
    """Parse a color and return every representation of it."""
    r, g, b, a = parse_color(text)
    h, s, l = rgb_to_hsl(r, g, b)
    hv, sv, vv = rgb_to_hsv(r, g, b)
    c, m, y, k = rgb_to_cmyk(r, g, b)
    hex_str = to_hex(r, g, b)
    name = _HEX_TO_NAME.get(hex_str[1:]) if a == 1 else None

    rgb_str = (f"rgb({r}, {g}, {b})" if a == 1
               else f"rgba({r}, {g}, {b}, {a:g})")
    hsl_str = (f"hsl({h:g}, {s:g}%, {l:g}%)" if a == 1
               else f"hsla({h:g}, {s:g}%, {l:g}%, {a:g})")

    return {
        "r": r, "g": g, "b": b, "a": a,
        "hex": to_hex(r, g, b, a),
        "hex6": hex_str,
        "rgb": rgb_str,
        "hsl": hsl_str,
        "hsv": f"hsv({hv:g}, {sv:g}%, {vv:g}%)",
        "cmyk": f"cmyk({c:g}%, {m:g}%, {y:g}%, {k:g}%)",
        "name": name,
        "luminance": round(relative_luminance(r, g, b), 4),
    }


def contrast(fg_text, bg_text):
    """Contrast ratio + WCAG verdicts for a foreground over a background."""
    fg = parse_color(fg_text)
    bg = parse_color(bg_text)
    ratio = contrast_ratio(fg, bg)
    return {
        "ratio": ratio,
        "fg_hex": to_hex(*fg[:3]),
        "bg_hex": to_hex(*bg[:3]),
        "levels": wcag_levels(ratio),
    }


def convert_json(text):
    import json
    return json.dumps(convert(text))


def contrast_json(fg_text, bg_text):
    import json
    return json.dumps(contrast(fg_text, bg_text))


if __name__ == "__main__":
    # ── parsing across formats ──
    assert parse_color("#ff0000") == (255, 0, 0, 1.0)
    assert parse_color("#f00") == (255, 0, 0, 1.0)
    assert parse_color("#00ff0080")[:3] == (0, 255, 0)
    assert abs(parse_color("#00ff0080")[3] - 0.502) < 0.01
    assert parse_color("rgb(0, 0, 255)") == (0, 0, 255, 1.0)
    assert parse_color("rgba(0,0,255,0.5)") == (0, 0, 255, 0.5)
    assert parse_color("rgb(0 0 255 / 50%)") == (0, 0, 255, 0.5)
    assert parse_color("rgb(100%, 0%, 0%)") == (255, 0, 0, 1.0)
    assert parse_color("tomato") == (255, 99, 71, 1.0)
    assert parse_color("rebeccapurple") == (102, 51, 153, 1.0)

    # ── HSL round trips ──
    assert rgb_to_hsl(255, 0, 0) == (0.0, 100.0, 50.0)
    assert rgb_to_hsl(0, 255, 0) == (120.0, 100.0, 50.0)
    assert rgb_to_hsl(255, 255, 255) == (0.0, 0.0, 100.0)
    assert hsl_to_rgb(120, 100, 50) == (0, 255, 0)
    assert hsl_to_rgb(240, 100, 50) == (0, 0, 255)
    for col in [(255, 0, 0), (18, 52, 86), (200, 100, 50), (0, 0, 0)]:
        h, s, l = rgb_to_hsl(*col)
        back = hsl_to_rgb(h, s, l)
        assert all(abs(a - b) <= 1 for a, b in zip(col, back)), (col, back)

    # ── HSV & CMYK ──
    assert rgb_to_hsv(255, 0, 0) == (0.0, 100.0, 100.0)
    assert rgb_to_hsv(0, 0, 0) == (0.0, 0.0, 0.0)
    assert rgb_to_cmyk(255, 0, 0) == (0.0, 100.0, 100.0, 0.0)
    assert rgb_to_cmyk(0, 0, 0) == (0.0, 0.0, 0.0, 100.0)

    # ── contrast / WCAG ──
    assert contrast_ratio((0, 0, 0), (255, 255, 255)) == 21.0
    assert contrast_ratio((255, 255, 255), (255, 255, 255)) == 1.0
    lv = wcag_levels(21.0)
    assert all(lv.values())
    lv = wcag_levels(4.5)
    assert lv["aa_normal"] and not lv["aaa_normal"] and lv["aaa_large"]

    # ── full convert ──
    out = convert("#1e90ff")
    assert out["hex"] == "#1e90ff"
    assert out["name"] == "dodgerblue"
    assert out["rgb"] == "rgb(30, 144, 255)"
    print(f"#1e90ff -> {out['rgb']}  {out['hsl']}  {out['hsv']}  {out['cmyk']}")

    out = convert("rgba(255, 0, 0, 0.25)")
    assert out["hex"] == "#ff000040", out["hex"]
    assert out["rgb"] == "rgba(255, 0, 0, 0.25)"
    assert out["name"] is None  # translucent → no name match

    c = contrast("#777777", "#ffffff")
    print(f"#777 on #fff -> {c['ratio']}:1  {c['levels']}")

    # ── errors ──
    for bad in ["", "#12g", "notacolor", "rgb(1,2)", "hsl(1,2,3,4,5)"]:
        try:
            parse_color(bad)
            raise AssertionError(f"expected failure for {bad!r}")
        except ValueError as e:
            print(f"{bad!r:14s} -> {e}")

    print("all checks passed")
