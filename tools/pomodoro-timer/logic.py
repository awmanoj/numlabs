"""Pomodoro timer — pure-Python logic.

The Pomodoro Technique breaks work into fixed focus sprints separated by short
breaks, with a longer break after every few sprints. The classic settings are a
25-minute focus, a 5-minute short break, a 15-minute long break, and a long
break after every 4 focus sprints.

The *ticking* of a countdown belongs in the browser (it needs a clock and a
sound), but the parts that are actually decisions — how long each phase lasts,
which phase comes next, and how a full cycle adds up — are pure functions and
live here so they can be tested on their own:

  * :func:`duration_seconds` — length of a phase, in seconds, from the config.
  * :func:`next_state` — the phase-machine: given the phase that just ended and
    how many focus sprints are done, return the next phase to run.
  * :func:`cycle_plan` — the full work→break sequence of one long-break cycle,
    with focus / break / total minutes, for the "what a session looks like"
    summary.
  * :func:`format_time` — seconds → ``MM:SS`` for the big readout.

A "phase" is one of ``"work"``, ``"short_break"`` or ``"long_break"``.
"""

WORK = "work"
SHORT_BREAK = "short_break"
LONG_BREAK = "long_break"

_LABELS = {
    WORK: "Focus",
    SHORT_BREAK: "Short break",
    LONG_BREAK: "Long break",
}

# Sane bounds so a stray giant or zero value can't produce a broken timer.
_MIN_MINUTES = 1
_MAX_MINUTES = 180
_MIN_ROUNDS = 1
_MAX_ROUNDS = 12


def _clamp(value, lo, hi, default):
    """Coerce ``value`` to an int within ``[lo, hi]``; bad input → ``default``."""
    try:
        value = int(round(float(value)))
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, value))


def normalize_config(work=25, short_break=5, long_break=15, rounds=4):
    """Clamp raw user settings to a sane, well-typed config dict.

    ``rounds`` is the number of focus sprints between long breaks (i.e. a long
    break follows every Nth focus sprint).
    """
    return {
        "work": _clamp(work, _MIN_MINUTES, _MAX_MINUTES, 25),
        "short_break": _clamp(short_break, _MIN_MINUTES, _MAX_MINUTES, 5),
        "long_break": _clamp(long_break, _MIN_MINUTES, _MAX_MINUTES, 15),
        "rounds": _clamp(rounds, _MIN_ROUNDS, _MAX_ROUNDS, 4),
    }


def phase_label(phase):
    """Human-readable name for a phase."""
    return _LABELS.get(phase, "Focus")


def is_break(phase):
    """True for either kind of break, False for a focus sprint."""
    return phase in (SHORT_BREAK, LONG_BREAK)


def duration_seconds(phase, config):
    """Length of ``phase`` in seconds, from a (already normalized) config."""
    minutes = {
        WORK: config["work"],
        SHORT_BREAK: config["short_break"],
        LONG_BREAK: config["long_break"],
    }.get(phase, config["work"])
    return minutes * 60


def next_state(phase, completed_work, config):
    """The phase-machine: what to run after ``phase`` just finished.

    ``completed_work`` is the number of focus sprints completed *before* this
    transition. Returns a dict describing the next phase:

      * a finished **focus** sprint increments the completed count; the next
        phase is a long break when that count is a multiple of ``rounds``,
        otherwise a short break.
      * a finished **break** of either kind always returns to focus, leaving the
        completed count untouched.

    The returned ``round`` is the 1-based position of the *current/next focus
    sprint* within the long-break cycle, handy for a "Round 2 of 4" label.
    """
    rounds = config["rounds"]

    if phase == WORK:
        completed_work += 1
        nxt = LONG_BREAK if completed_work % rounds == 0 else SHORT_BREAK
    else:
        nxt = WORK

    # Position of the focus sprint we're in or heading toward, 1..rounds.
    round_in_cycle = (completed_work % rounds) + 1
    if nxt == WORK and completed_work % rounds == 0 and completed_work > 0:
        round_in_cycle = 1

    secs = duration_seconds(nxt, config)
    return {
        "phase": nxt,
        "completed_work": completed_work,
        "duration_seconds": secs,
        "label": phase_label(nxt),
        "is_break": is_break(nxt),
        "round": round_in_cycle,
        "rounds": rounds,
    }


def cycle_plan(config):
    """The full sequence of one long-break cycle, plus its time totals.

    A cycle is ``rounds`` focus sprints, each followed by a short break, except
    the last, which is followed by the long break. Returns a dict with the
    ordered ``steps`` (phase + minutes each) and ``focus_minutes``,
    ``break_minutes`` and ``total_minutes``.
    """
    rounds = config["rounds"]
    steps = []
    for i in range(1, rounds + 1):
        steps.append({"phase": WORK, "minutes": config["work"]})
        if i == rounds:
            steps.append({"phase": LONG_BREAK, "minutes": config["long_break"]})
        else:
            steps.append({"phase": SHORT_BREAK, "minutes": config["short_break"]})

    focus_minutes = sum(s["minutes"] for s in steps if s["phase"] == WORK)
    break_minutes = sum(s["minutes"] for s in steps if s["phase"] != WORK)
    return {
        "steps": steps,
        "focus_minutes": focus_minutes,
        "break_minutes": break_minutes,
        "total_minutes": focus_minutes + break_minutes,
    }


def format_time(seconds):
    """Seconds → ``MM:SS`` (minutes can exceed 99 for very long phases)."""
    seconds = max(0, int(round(seconds)))
    minutes, secs = divmod(seconds, 60)
    return f"{minutes:02d}:{secs:02d}"


if __name__ == "__main__":
    cfg = normalize_config()
    assert cfg == {"work": 25, "short_break": 5, "long_break": 15, "rounds": 4}, cfg

    # Durations come straight from the config, in seconds.
    assert duration_seconds(WORK, cfg) == 25 * 60
    assert duration_seconds(SHORT_BREAK, cfg) == 5 * 60
    assert duration_seconds(LONG_BREAK, cfg) == 15 * 60

    # Walk a full cycle: work → short → work → short → work → short → work → long.
    phase, done = WORK, 0
    seq = []
    for _ in range(8):
        s = next_state(phase, done, cfg)
        seq.append(s["phase"])
        phase, done = s["phase"], s["completed_work"]
    assert seq == [
        SHORT_BREAK, WORK, SHORT_BREAK, WORK,
        SHORT_BREAK, WORK, LONG_BREAK, WORK,
    ], seq
    # Four focus sprints completed across that walk.
    assert done == 4, done

    # The long break lands exactly on the rounds-th sprint, not before.
    assert next_state(WORK, 0, cfg)["phase"] == SHORT_BREAK
    assert next_state(WORK, 3, cfg)["phase"] == LONG_BREAK  # 4th sprint done
    assert next_state(WORK, 3, cfg)["completed_work"] == 4

    # Round numbering counts the focus sprint we're in / heading to.
    assert next_state(SHORT_BREAK, 1, cfg)["round"] == 2  # heading into sprint 2
    assert next_state(LONG_BREAK, 4, cfg)["round"] == 1   # cycle restarts

    # A custom config with rounds=2 long-breaks twice as often.
    cfg2 = normalize_config(work=50, short_break=10, long_break=30, rounds=2)
    assert next_state(WORK, 1, cfg2)["phase"] == LONG_BREAK

    # Cycle plan sums up correctly: 4×25 focus, 3×5 + 1×15 break.
    plan = cycle_plan(cfg)
    assert plan["focus_minutes"] == 100, plan
    assert plan["break_minutes"] == 30, plan
    assert plan["total_minutes"] == 130, plan
    assert len(plan["steps"]) == 8
    assert plan["steps"][-1]["phase"] == LONG_BREAK

    # Clamping: nonsense and out-of-range values fall back to safe numbers.
    bad = normalize_config(work=0, short_break=9999, long_break="x", rounds=0)
    assert bad["work"] == _MIN_MINUTES
    assert bad["short_break"] == _MAX_MINUTES
    assert bad["long_break"] == 15
    assert bad["rounds"] == _MIN_ROUNDS

    # Time formatting, including over an hour.
    assert format_time(0) == "00:00"
    assert format_time(5) == "00:05"
    assert format_time(65) == "01:05"
    assert format_time(25 * 60) == "25:00"
    assert format_time(125 * 60) == "125:00"
    assert format_time(-3) == "00:00"

    print("all checks passed")
