"""Roman numeral converter — pure-Python logic.

Converts both directions:
  - integer (1..3999) -> Roman numeral
  - Roman numeral     -> integer

Standard (classical) Roman numerals only: the symbols I, V, X, L, C, D, M,
with subtractive pairs IV, IX, XL, XC, CD, CM. The largest value a single
M-run can express is 3999 (MMMCMXCIX), so we cap there — beyond that you
need vinculum/overline notation, which plain text can't represent.
"""

MIN_N = 1
MAX_N = 3999

# Ordered high -> low so a greedy pass emits the canonical form.
_NUMERALS = [
    (1000, "M"),
    (900, "CM"),
    (500, "D"),
    (400, "CD"),
    (100, "C"),
    (90, "XC"),
    (50, "L"),
    (40, "XL"),
    (10, "X"),
    (9, "IX"),
    (5, "V"),
    (4, "IV"),
    (1, "I"),
]

_VALUE = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def to_roman(n):
    """Integer (1..3999) -> canonical Roman numeral string."""
    if not isinstance(n, int):
        n = int(n)
    if n < MIN_N or n > MAX_N:
        raise ValueError(f"n must be an integer between {MIN_N} and {MAX_N}")

    out = []
    for value, symbol in _NUMERALS:
        count, n = divmod(n, value)
        out.append(symbol * count)
    return "".join(out)


def from_roman(s):
    """Roman numeral string -> integer. Validates canonical form."""
    if not isinstance(s, str):
        s = str(s)
    s = s.strip().upper()
    if not s:
        raise ValueError("Enter a Roman numeral")

    for ch in s:
        if ch not in _VALUE:
            raise ValueError(f"'{ch}' is not a Roman numeral symbol")

    # Sum with the subtractive rule: a smaller symbol before a larger one
    # is subtracted (IV = 4), otherwise added.
    total = 0
    prev = 0
    for ch in reversed(s):
        value = _VALUE[ch]
        if value < prev:
            total -= value
        else:
            total += value
            prev = value

    # Reject non-canonical spellings (IIII, VX, etc.) by round-tripping.
    if total < MIN_N or total > MAX_N or to_roman(total) != s:
        raise ValueError(f"'{s}' is not a valid Roman numeral")

    return total


if __name__ == "__main__":
    samples = [1, 4, 9, 14, 40, 90, 400, 944, 1994, 2024, 3888, 3999]
    for n in samples:
        r = to_roman(n)
        assert from_roman(r) == n, (n, r)
        print(f"{n:>5} = {r}")

    # round-trip every value in range
    for n in range(MIN_N, MAX_N + 1):
        assert from_roman(to_roman(n)) == n, n
    print(f"round-trip ok for {MIN_N}..{MAX_N}")

    # error cases
    for bad in (0, 4000, -3):
        try:
            to_roman(bad)
        except ValueError as e:
            print(f"to_roman({bad}): {e}")
    for bad in ("", "IIII", "VX", "ABC", "MMMM"):
        try:
            from_roman(bad)
        except ValueError as e:
            print(f"from_roman({bad!r}): {e}")
