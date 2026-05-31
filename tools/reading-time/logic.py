"""Reading time estimator — pure-Python logic.

Given a block of text and a reading speed, estimate how long it takes to read
(silently) and to speak aloud, alongside the usual text stats: words,
characters (with and without spaces), sentences, and paragraphs.

The math is deliberately simple — reading time is just ``words / wpm`` — but the
counting is done carefully:

  * **words** are runs of non-whitespace separated by whitespace, matching how
    word counters in editors behave; numbers and hyphenated tokens count once.
  * **sentences** are runs ended by ``.``, ``!`` or ``?`` (one or more), so
    ellipses and ``?!`` don't inflate the count; a trailing fragment with no
    terminator still counts as one sentence.
  * **paragraphs** are blocks separated by one or more blank lines.

Typical adult silent reading is ~200–250 words per minute (wpm); 230 is a common
default. Speaking aloud is slower — ~130 wpm is a standard presentation pace —
so the speaking estimate uses its own rate.
"""

import re

# Sane bounds so a stray "0" or a pasted-in huge number can't produce nonsense.
_MIN_WPM = 50
_MAX_WPM = 1000

_SENTENCE_END = re.compile(r"[.!?]+")
_PARAGRAPH_SPLIT = re.compile(r"\n\s*\n")


def _clamp_wpm(wpm):
    """Coerce wpm to an int within sane bounds, defaulting bad input to 230."""
    try:
        wpm = int(round(float(wpm)))
    except (TypeError, ValueError):
        return 230
    return max(_MIN_WPM, min(_MAX_WPM, wpm))


def _format_duration(seconds):
    """Human-readable label for a duration in seconds.

    Rounds to whole seconds. Under a minute reads as "X sec"; a minute or more
    reads as "M min S sec" (dropping the seconds when they're zero).
    """
    seconds = int(round(seconds))
    if seconds <= 0:
        return "0 sec"
    if seconds < 60:
        return f"{seconds} sec"
    minutes, secs = divmod(seconds, 60)
    if secs == 0:
        return f"{minutes} min"
    return f"{minutes} min {secs} sec"


def estimate(text, wpm=230, speaking_wpm=130):
    """Estimate reading/speaking time and text stats for ``text``.

    ``wpm`` is the silent reading speed; ``speaking_wpm`` the spoken pace. Both
    are clamped to a sane range. Returns a dict of counts, raw durations in
    seconds, and pre-formatted human-readable labels.
    """
    if not isinstance(text, str):
        text = str(text)

    wpm = _clamp_wpm(wpm)
    speaking_wpm = _clamp_wpm(speaking_wpm)

    words = len(text.split())
    chars = len(text)
    chars_no_spaces = len("".join(text.split()))

    stripped = text.strip()
    # Count sentence terminators, but a non-empty fragment with no terminator
    # (e.g. a heading or a single clause) still counts as one sentence.
    if stripped:
        sentences = len(_SENTENCE_END.findall(stripped))
        if sentences == 0:
            sentences = 1
        paragraphs = len([p for p in _PARAGRAPH_SPLIT.split(stripped) if p.strip()])
    else:
        sentences = 0
        paragraphs = 0

    reading_seconds = words / wpm * 60
    speaking_seconds = words / speaking_wpm * 60

    return {
        "words": words,
        "chars": chars,
        "chars_no_spaces": chars_no_spaces,
        "sentences": sentences,
        "paragraphs": paragraphs,
        "wpm": wpm,
        "speaking_wpm": speaking_wpm,
        "reading_seconds": reading_seconds,
        "speaking_seconds": speaking_seconds,
        "reading_label": _format_duration(reading_seconds),
        "speaking_label": _format_duration(speaking_seconds),
    }


if __name__ == "__main__":
    # 230 words at 230 wpm is exactly one minute.
    text_230 = " ".join(["word"] * 230)
    r = estimate(text_230, wpm=230)
    assert r["words"] == 230, r["words"]
    assert r["reading_label"] == "1 min", r["reading_label"]

    # Basic counts on a small passage.
    sample = "Hello world. This is a test! Is it working?\n\nA second paragraph."
    r = estimate(sample)
    assert r["words"] == 12, r["words"]
    assert r["sentences"] == 4, r["sentences"]  # three terminators + final fragment
    assert r["paragraphs"] == 2, r["paragraphs"]
    assert r["chars_no_spaces"] < r["chars"]

    # Empty input is all zeros, no crash.
    r = estimate("")
    assert r["words"] == 0 and r["sentences"] == 0 and r["paragraphs"] == 0
    assert r["reading_label"] == "0 sec"

    # A single unterminated clause counts as one sentence.
    r = estimate("Just a heading with no period")
    assert r["sentences"] == 1, r["sentences"]
    assert r["paragraphs"] == 1, r["paragraphs"]

    # Ellipses and ?! don't inflate the sentence count.
    r = estimate("Wait... really?! Yes.")
    assert r["sentences"] == 3, r["sentences"]

    # wpm is clamped to bounds; non-numeric input falls back to the default.
    assert estimate("a b c", wpm=0)["wpm"] == _MIN_WPM
    assert estimate("a b c", wpm=99999)["wpm"] == _MAX_WPM
    assert estimate("a b c", wpm="fast")["wpm"] == 230
    big = estimate(" ".join(["w"] * 1300))
    assert big["speaking_seconds"] > big["reading_seconds"]

    # Sub-minute durations read in seconds.
    assert _format_duration(45) == "45 sec"
    assert _format_duration(90) == "1 min 30 sec"
    assert _format_duration(120) == "2 min"

    print("all checks passed")
