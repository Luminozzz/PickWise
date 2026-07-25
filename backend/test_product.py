"""
Regression tests for product_detail() — the per-mouse spec rows + criteria
tags behind the product detail page.

Run from the backend/ directory:
    python test_product.py          # runs every test_* below, exits non-zero on failure
    pytest test_product.py          # same tests, discovered by name

Reuses the mock mice from test_recommend, so there's no database here either.
"""

import sys, os

BACKEND = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND)
for _p in (PROJECT_ROOT, BACKEND, os.path.join(BACKEND, "algorithm")):
    sys.path.insert(0, _p)

from test_recommend import MICE, PAYLOADS
from algorithm.recommend import product_detail, build_facts, _IMPORTANCE, _DEFAULT_ORDER, _HIDDEN_FROM_TAGS
from algorithm.classes import User_Type
from algorithm import config

_GAMER = PAYLOADS["FPS gamer (medium hand, prefers wireless, lightweight, no RGB)"]
# The Superlight carries gaming_specs (so it has a tracking speed); the MX Master
# has none (so tracking must be absent from its rows entirely).
_LIGHT, _HEAVY = MICE[0], MICE[2]


def _facts(payload=None):
    # prices left empty on purpose: no live DB, and it exercises the "no price
    # data -> row dropped" path.
    return build_facts({**(payload or {}), "prices": {}})


def test_missing_spec_row_is_dropped():
    """The MX Master has no gaming_specs, so it reports no tracking speed —
    unlike compare_detail, a single mouse's own missing spec just disappears."""
    rows = product_detail(_HEAVY, _facts(_GAMER))["details"]
    assert not any(r["key"] == "tracking" for r in rows), "MX Master has no tracking speed"
    rows_light = product_detail(_LIGHT, _facts(_GAMER))["details"]
    assert any(r["key"] == "tracking" for r in rows_light), "Superlight should report tracking speed"


def test_hidden_rule_excluded_from_criteria():
    """VALUE_FOR_MONEY feeds the score but has no chip of its own."""
    tags = product_detail(_LIGHT, _facts(_GAMER))["criteria"]
    assert config.VALUE in _HIDDEN_FROM_TAGS
    ids = {t["label"] for t in tags}
    assert "Value for money" not in ids



def test_no_answers_gives_none_status():
    """With no quiz answers, specs still show but there's nothing to judge them
    against, so every row status is 'none'."""
    rows = product_detail(_LIGHT, _facts(None))["details"]
    assert rows and all(r["status"] == "none" for r in rows)


if __name__ == "__main__":
    _tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for _t in _tests:
        _t()
        print("OK", _t.__name__)
    print("ALL PASSED")
