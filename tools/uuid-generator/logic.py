"""UUID generator — pure-Python logic.

Generates RFC 4122 / RFC 9562 UUIDs in several versions:

  * **v4** — random. The everyday choice: 122 bits of randomness, no
    coordination needed, collisions are astronomically unlikely.
  * **v7** — time-ordered. A 48-bit Unix-millisecond timestamp followed by
    random bits, so freshly minted values sort by creation time. Great as a
    database primary key — index-friendly without leaking a MAC address.
  * **v1** — time + node. Legacy timestamp UUID. In the browser the node is
    a random (multicast) value, not a hardware MAC.
  * **nil** — the all-zero UUID, ``00000000-0000-0000-0000-000000000000``.

Output formatting is independent of the version: case (lower / UPPER) and
whether the hyphen separators are kept.

The standard library ``uuid`` module covers v4/v1/nil exactly; v7 is assembled
by hand from the bit layout in RFC 9562 §5.7, since stdlib has no ``uuid7``.
"""

import secrets
import time
import uuid

MAX_COUNT = 1000


def _uuid7():
    """Build a version-7 (time-ordered) UUID per RFC 9562 §5.7.

    Layout (128 bits, most-significant first):
      48 bits  unix timestamp in milliseconds
       4 bits  version (0b0111)
      12 bits  rand_a
       2 bits  variant (0b10)
      62 bits  rand_b
    """
    ms = int(time.time() * 1000) & 0xFFFFFFFFFFFF
    rand_a = secrets.randbits(12)
    rand_b = secrets.randbits(62)

    value = ms << 80
    value |= 0x7 << 76          # version nibble
    value |= rand_a << 64
    value |= 0b10 << 62         # variant bits
    value |= rand_b
    return uuid.UUID(int=value)


def _make(version):
    """Return a fresh ``uuid.UUID`` for the requested version string."""
    if version == "4":
        return uuid.uuid4()
    if version == "7":
        return _uuid7()
    if version == "1":
        return uuid.uuid1()
    if version == "nil":
        return uuid.UUID(int=0)
    raise ValueError(f"Unknown UUID version: {version!r}")


def _format(u, uppercase, hyphens):
    """Render a UUID as text with the chosen case and separator style."""
    text = str(u)
    if not hyphens:
        text = text.replace("-", "")
    if uppercase:
        text = text.upper()
    return text


def generate(version="4", count=1, uppercase=False, hyphens=True):
    """Generate ``count`` UUIDs of ``version`` and return them plus metadata.

    ``version`` is ``"4"``, ``"7"``, ``"1"`` or ``"nil"``. ``count`` is clamped
    to ``[1, MAX_COUNT]``; anything outside raises ValueError so the UI can show
    a clear message. Returns a dict with the list, a newline-joined ``text``
    block, and the effective count/version.
    """
    try:
        count = int(count)
    except (TypeError, ValueError):
        raise ValueError("Count must be a whole number")
    if count < 1:
        raise ValueError("Generate at least one UUID")
    if count > MAX_COUNT:
        raise ValueError(f"Too many at once — keep it to {MAX_COUNT} or fewer")

    uuids = [_format(_make(version), uppercase, hyphens) for _ in range(count)]

    return {
        "uuids": uuids,
        "text": "\n".join(uuids),
        "count": len(uuids),
        "version": version,
    }


if __name__ == "__main__":
    import re

    # v4 is random, well-formed, and version/variant bits are correct
    r = generate("4")
    one = r["uuids"][0]
    assert r["count"] == 1
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        one,
    ), one
    print(one)

    # two successive v4s differ
    assert generate("4")["uuids"][0] != generate("4")["uuids"][0]

    # v7 has version nibble 7, the 10xx variant, and is monotonic-ish in time
    u7 = uuid.UUID(generate("7")["uuids"][0])
    assert u7.version == 7, u7.version
    assert (u7.int >> 62) & 0b11 == 0b10        # variant
    a = _uuid7()
    time.sleep(0.002)
    b = _uuid7()
    assert b.int > a.int, "v7 should sort by time"

    # v1 is a valid timestamp UUID
    assert uuid.UUID(generate("1")["uuids"][0]).version == 1

    # nil is all zeros
    assert generate("nil")["uuids"][0] == "00000000-0000-0000-0000-000000000000"

    # formatting: uppercase + no hyphens gives a 32-char hex blob
    f = generate("4", count=1, uppercase=True, hyphens=False)["uuids"][0]
    assert re.fullmatch(r"[0-9A-F]{32}", f), f

    # bulk generation returns the right count and a matching text block
    bulk = generate("4", count=5)
    assert bulk["count"] == 5
    assert bulk["text"].count("\n") == 4
    assert len(set(bulk["uuids"])) == 5      # all distinct

    # error cases
    for bad in [("4", 0), ("4", -3), ("4", MAX_COUNT + 1), ("9", 1)]:
        try:
            generate(bad[0], count=bad[1])
            raise AssertionError(f"expected failure for {bad!r}")
        except ValueError as e:
            print(f"generate{bad!r}: {e}")

    print("all checks passed")
