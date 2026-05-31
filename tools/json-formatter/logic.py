"""JSON formatter / validator — pure-Python logic.

Parses a JSON document and re-serializes it, either pretty-printed with a
chosen indentation or minified to the most compact form. Parsing is done with
the standard-library ``json`` module, so validation is exactly as strict as
Python's parser: a single source of truth, no hand-rolled tokenizer.

On invalid input we surface the parser's own line/column/message so the user
can find the offending character, rather than a generic "invalid JSON".
"""

import json

# indent_mode -> the value handed to json.dumps(indent=...).
#   "2" / "4"  -> that many spaces
#   "tab"      -> a literal tab
#   "min"      -> None + compact separators (handled in format_json)
_INDENTS = {"2": 2, "4": 4, "tab": "\t"}


def _depth(obj):
    """Maximum nesting depth of a parsed JSON value (a scalar is depth 1)."""
    if isinstance(obj, dict):
        return 1 + max((_depth(v) for v in obj.values()), default=0)
    if isinstance(obj, list):
        return 1 + max((_depth(v) for v in obj), default=0)
    return 1


def _count_nodes(obj):
    """Total number of values in the tree — containers and scalars alike."""
    if isinstance(obj, dict):
        return 1 + sum(_count_nodes(v) for v in obj.values())
    if isinstance(obj, list):
        return 1 + sum(_count_nodes(v) for v in obj)
    return 1


def format_json(text, indent_mode="2", sort_keys=False):
    """Validate and re-serialize a JSON string.

    Returns a dict with the formatted ``output`` and a few stats about the
    document. Raises ValueError with a human-readable, located message when
    the input is not valid JSON.
    """
    if not isinstance(text, str):
        text = str(text)
    if not text.strip():
        raise ValueError("Nothing to format — paste some JSON first")

    try:
        obj = json.loads(text)
    except json.JSONDecodeError as e:
        # e.msg is the bare reason ("Expecting ',' delimiter"); add position.
        raise ValueError(f"{e.msg} (line {e.lineno}, column {e.colno})")

    if indent_mode == "min":
        # Most compact form: no spaces after separators.
        output = json.dumps(
            obj, separators=(",", ":"), sort_keys=sort_keys, ensure_ascii=False
        )
    else:
        indent = _INDENTS.get(indent_mode, 2)
        output = json.dumps(
            obj, indent=indent, sort_keys=sort_keys, ensure_ascii=False
        )

    return {
        "output": output,
        "bytes": len(output.encode("utf-8")),
        "lines": output.count("\n") + 1,
        "nodes": _count_nodes(obj),
        "depth": _depth(obj),
    }


if __name__ == "__main__":
    sample = '{"b":1,"a":[2,3,{"x":true,"y":null}],"c":"héllo"}'

    pretty = format_json(sample, indent_mode="2")
    print(pretty["output"])
    assert pretty["lines"] > 1
    assert pretty["depth"] == 4, pretty["depth"]  # dict -> list -> dict -> scalar
    # b, a, [2,3,{...}] -> a(list)+2+3+{}(x,y) , c  : count them
    assert pretty["nodes"] == _count_nodes(json.loads(sample))

    # sort_keys reorders top-level keys a, b, c
    sorted_out = format_json(sample, indent_mode="2", sort_keys=True)["output"]
    assert sorted_out.index('"a"') < sorted_out.index('"b"') < sorted_out.index('"c"')

    # minify round-trips to the same object and has no newlines
    mini = format_json(sample, indent_mode="min")["output"]
    assert "\n" not in mini
    assert json.loads(mini) == json.loads(sample)

    # tab indentation
    tabbed = format_json('{"k":1}', indent_mode="tab")["output"]
    assert "\t" in tabbed

    # non-ASCII is preserved, not \u-escaped
    assert "héllo" in pretty["output"]

    # error cases carry line/column
    for bad in ("{", "{'a':1}", '{"a":1,}', "[1 2]", ""):
        try:
            format_json(bad)
            raise AssertionError(f"expected failure for {bad!r}")
        except ValueError as e:
            print(f"format_json({bad!r}): {e}")

    print("all checks passed")
