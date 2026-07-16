"""
Regression tests for compare_detail() — the aligned, importance-ordered spec
rows behind the /compare page.

Run from the backend/ directory:
    python test_compare.py          # runs every test_* below, exits non-zero on failure
    pytest test_compare.py          # same tests, discovered by name

Reuses the mock mice from test_recommend, so there's no database here either.
"""

import sys, os

BACKEND = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND)
for _p in (PROJECT_ROOT, BACKEND, os.path.join(BACKEND, "algorithm")):
    sys.path.insert(0, _p)

from test_recommend import MICE, PAYLOADS
from algorithm.recommend import compare_detail, build_facts, _IMPORTANCE, _DEFAULT_ORDER
from algorithm.classes import User_Type

_GAMER = PAYLOADS["FPS gamer (medium hand, prefers wireless, lightweight, no RGB)"]
# The Superlight carries gaming_specs (so it has a tracking speed); the MX Master
# has none (so it doesn't). That asymmetry is what the alignment tests hinge on.
_LIGHT, _HEAVY = MICE[0], MICE[2]


def _facts(payload=None):
    # prices left empty on purpose: no live DB, and it exercises the "row present
    # for nobody -> dropped" path for the Price row.
    return build_facts({**(payload or {}), "prices": {}})


def test_rows_are_aligned_one_cell_per_mouse():
    """Every row must have exactly one cell per mouse, each a {value, status}
    pair — this is what lets the frontend zip rows into columns safely."""
    rows = compare_detail([_LIGHT, _HEAVY], _facts(_GAMER))
    assert rows, "expected some rows"
    for r in rows:
        assert len(r["cells"]) == 2, f"{r['key']}: {len(r['cells'])} cells for 2 mice"
        for c in r["cells"]:
            assert set(c.keys()) == {"value", "status"}, f"{r['key']}: bad cell shape {c}"


def test_missing_spec_keeps_row_with_null_cell():
    """The MX Master has no tracking speed. The row must survive for the group
    (the Superlight has one) and the missing mouse gets a null cell — otherwise
    the row would vanish and shift every column below it out of alignment."""
    rows = compare_detail([_LIGHT, _HEAVY], _facts(_GAMER))
    tracking = next((r for r in rows if r["key"] == "tracking"), None)
    assert tracking is not None, "tracking row should survive because one mouse has it"
    assert tracking["cells"][0]["value"] is not None, "Superlight should report a tracking speed"
    assert tracking["cells"][1]["value"] is None, "MX Master has none -> null cell"
    assert tracking["cells"][1]["status"] == "none", "a spec a mouse lacks can't fit or misfit"


def test_row_dropped_only_when_nobody_has_it():
    """Neither mock mouse has a price here, so the Price row should not appear."""
    rows = compare_detail([_LIGHT, _HEAVY], _facts(_GAMER))
    assert not any(r["key"] == "price" for r in rows), "price row should drop when no mouse has one"


def test_gamer_order_follows_importance():
    """Rows are ordered by what matters to a gamer: performance first, not price."""
    rows = compare_detail([_LIGHT, _HEAVY], _facts(_GAMER))
    present = [r["key"] for r in rows]
    expected = [k for k in _IMPORTANCE[User_Type.GAMER] if k in present]
    assert present == expected, f"gamer row order {present} != importance {expected}"
    assert present[0] == "max_DPI", "a gamer should see Max DPI first"


def test_no_quiz_falls_back_to_default_order():
    """With no answers, rows follow the general default importance order."""
    rows = compare_detail([_LIGHT, _HEAVY], _facts(None))
    present = [r["key"] for r in rows]
    expected = [k for k in _DEFAULT_ORDER if k in present]
    assert present == expected, f"default row order {present} != {expected}"


def test_single_mouse():
    rows = compare_detail([_LIGHT], _facts(_GAMER))
    assert rows and all(len(r["cells"]) == 1 for r in rows)


def test_empty_mice():
    assert compare_detail([], _facts(_GAMER)) == []


if __name__ == "__main__":
    _tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for _t in _tests:
        _t()
        print("OK", _t.__name__)
    print("ALL PASSED")
