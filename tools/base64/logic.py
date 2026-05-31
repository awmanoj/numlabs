"""Base64 encoder / decoder — pure-Python logic.

Encodes text to Base64 or decodes Base64 back to text, using the standard
library ``base64`` module so the transform is exactly RFC 4648. Text is treated
as UTF-8 on the way in and out, which is what every browser and web API expects.

Two alphabets are supported:
  * **standard** — the classic ``+`` / ``/`` alphabet.
  * **url-safe** — ``-`` / ``_`` instead, for use in URLs, JWTs, and filenames.

Decoding is deliberately forgiving: surrounding whitespace and newlines are
stripped (MIME-wrapped Base64 has line breaks), missing ``=`` padding is
restored, and either alphabet is accepted regardless of the chosen variant.
"""

import base64
import binascii


def _encode(text, urlsafe):
    """Encode a (unicode) string to Base64 text."""
    raw = text.encode("utf-8")
    if urlsafe:
        out = base64.urlsafe_b64encode(raw)
    else:
        out = base64.b64encode(raw)
    return out.decode("ascii"), len(raw)


def _decode(text, urlsafe):
    """Decode Base64 text back to a (unicode) string.

    Tolerates whitespace/newlines and missing padding, and accepts either
    alphabet so a value pasted from a URL still decodes when "standard" is set.
    """
    # Drop all ASCII whitespace — MIME Base64 wraps at 76 columns.
    compact = "".join(text.split())
    if not compact:
        raise ValueError("Nothing to decode — paste some Base64 first")

    # Normalise both alphabets to the standard one so a single decoder handles
    # whatever the user pasted, regardless of the selected variant.
    compact = compact.replace("-", "+").replace("_", "/")

    # Restore stripped '=' padding (Base64 length must be a multiple of 4).
    pad = (-len(compact)) % 4
    compact += "=" * pad

    try:
        raw = base64.b64decode(compact, validate=True)
    except (binascii.Error, ValueError):
        raise ValueError("Not valid Base64 — check for stray characters")

    try:
        return raw.decode("utf-8"), len(raw)
    except UnicodeDecodeError:
        raise ValueError("Decoded bytes are not valid UTF-8 text")


def convert(text, mode="encode", variant="standard"):
    """Encode or decode ``text`` and return the result plus byte counts.

    ``mode`` is ``"encode"`` or ``"decode"``; ``variant`` is ``"standard"`` or
    ``"urlsafe"``. Raises ValueError with a human-readable message on bad input.
    """
    if not isinstance(text, str):
        text = str(text)
    urlsafe = variant == "urlsafe"

    if mode == "encode":
        if not text:
            raise ValueError("Nothing to encode — type some text first")
        output, in_bytes = _encode(text, urlsafe)
    elif mode == "decode":
        output, in_bytes = _decode(text, urlsafe)
    else:
        raise ValueError(f"Unknown mode: {mode!r}")

    return {
        "output": output,
        "in_bytes": in_bytes,
        "out_bytes": len(output.encode("utf-8")),
        "chars": len(output),
    }


if __name__ == "__main__":
    # round-trip a simple ASCII string
    enc = convert("Hello, World!", mode="encode")
    assert enc["output"] == "SGVsbG8sIFdvcmxkIQ==", enc["output"]
    dec = convert(enc["output"], mode="decode")
    assert dec["output"] == "Hello, World!", dec["output"]
    print(enc["output"])

    # non-ASCII / emoji survives a UTF-8 round trip
    s = "héllo 世界 🚀"
    assert convert(convert(s, mode="encode")["output"], mode="decode")["output"] == s

    # url-safe alphabet uses - and _ instead of + and / , and decodes back
    raw_url = convert("<<<???>>>", mode="encode", variant="urlsafe")["output"]
    assert "+" not in raw_url and "/" not in raw_url
    assert convert(raw_url, mode="decode", variant="urlsafe")["output"] == "<<<???>>>"

    # decoder tolerates whitespace, newlines, and missing padding
    assert convert("SGVs bG8s\nIFdv cmxk IQ", mode="decode")["output"] == "Hello, World!"

    # decoder accepts url-safe input even when "standard" is selected
    assert convert(raw_url, mode="decode", variant="standard")["output"] == "<<<???>>>"

    # byte counts are reported
    assert enc["in_bytes"] == 13 and enc["out_bytes"] == len(enc["output"])

    # error cases
    for bad_args in [("", "encode"), ("", "decode"), ("!!!!", "decode"),
                     ("////", "decode")]:
        try:
            convert(bad_args[0], mode=bad_args[1])
            raise AssertionError(f"expected failure for {bad_args!r}")
        except ValueError as e:
            print(f"convert{bad_args!r}: {e}")

    print("all checks passed")
