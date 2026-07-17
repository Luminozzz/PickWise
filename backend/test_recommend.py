"""
Regression tests for backend/algorithm/recommend.py.

Run from the backend/ directory:
    python test_recommend.py        # runs every test_* below, exits non-zero on failure
    pytest test_recommend.py        # same tests, discovered by name

Uses mock Mouse objects so no real database is needed.
Budget is intentionally omitted from the payload to skip the
Price_History.query call (which requires a live DB/app context).

These pin *behaviour*, not exact scores: the lightweight mouse must rank first
for a weight-conscious gamer, results must come back sorted, every candidate
must survive. Exact score numbers are deliberately not asserted — the scoring
weights are allowed to change without tripping the whole suite red.
"""

import sys, os

# This file lives in backend/, so:
#   BACKEND = .../PickWise/backend
#   PROJECT_ROOT = .../PickWise
BACKEND = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND)

# Three roots needed by the algorithm's mixed import style:
#   import config                       -> backend/algorithm/config.py
#   from database.models import ...     -> backend/database/models.py
#   from backend.database.models import -> project root
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, BACKEND)
sys.path.insert(0, os.path.join(BACKEND, "algorithm"))

from types import SimpleNamespace
from database.models import Ergonomy
from algorithm.recommend import recommend


def _conn(bluetooth=False, dongle=False, wired=True):
    return SimpleNamespace(bluetooth=bluetooth, dongle=dongle, wired=wired)

def _gaming(rgb=False, tracking_speed=400, max_polling_rate=1000):
    return SimpleNamespace(rgb=rgb, tracking_speed=tracking_speed, max_polling_rate=max_polling_rate)

def _mouse(id, product_name, brand_name, *,
           length=120, weight=90, left_fit=False,
           ergonomy=Ergonomy.SYMMETRICAL, max_DPI=8000,
           number_of_buttons=3, min_battery_life=50,
           connectivity=None, gaming_specs=None):
    return SimpleNamespace(
        id=id,
        product_name=product_name,
        brand_name=brand_name,
        length=length,
        weight=weight,
        left_fit=left_fit,
        ergonomy=ergonomy,
        max_DPI=max_DPI,
        number_of_buttons=number_of_buttons,
        min_battery_life=min_battery_life,
        connectivity=connectivity or _conn(),
        gaming_specs=gaming_specs,
    )


MICE = [
    _mouse(1, "G Pro X Superlight 2", "Logitech",
           length=125, weight=60, max_DPI=32000, min_battery_life=95,
           connectivity=_conn(dongle=True),
           gaming_specs=_gaming(rgb=False, tracking_speed=500)),

    _mouse(2, "DeathAdder V3 HyperSpeed", "Razer",
           length=128, weight=88, max_DPI=30000, min_battery_life=90,
           connectivity=_conn(dongle=True),
           gaming_specs=_gaming(rgb=True, tracking_speed=450)),

    _mouse(3, "MX Master 3S", "Logitech",
           length=124, weight=141, max_DPI=8000, min_battery_life=70,
           connectivity=_conn(bluetooth=True, dongle=True)),

    _mouse(4, "Basilisk V3 X HyperSpeed", "Razer",
           length=130, weight=95, max_DPI=18000, min_battery_life=100,
           connectivity=_conn(dongle=True),
           gaming_specs=_gaming(rgb=True, tracking_speed=400)),
]


PAYLOADS = {
    "FPS gamer (medium hand, prefers wireless, lightweight, no RGB)": {
        "hand_size":   "medium",
        "wireless":    "preferably",
        "left_hand":   False,
        "user_type":   "gamer",
        "type_of_game": "fps",
        "light_weight": True,
        "rgb":          False,
    },
    "Office worker (large hand, wired OK, long hours, extra buttons)": {
        "hand_size":    "large",
        "wireless":     "no",
        "left_hand":    False,
        "user_type":    "office_worker",
        "hours_worked": "often",
        "extra_buttons": "preferably",
    },
    "Student (small hand, prefers wireless, travels often)": {
        "hand_size":          "small",
        "wireless":           "yes",
        "left_hand":          False,
        "user_type":          "student",
        "travel_portability": "often",
        "extra_buttons":      "no",
    },
}


_GAMER = "FPS gamer (medium hand, prefers wireless, lightweight, no RGB)"
_STUDENT = "Student (small hand, prefers wireless, travels often)"

# Ids in MICE: 1 = 60g Superlight, 2 = 88g DeathAdder, 3 = 141g MX Master, 4 = 95g Basilisk.
_LIGHTEST, _HEAVIEST = 1, 3


def test_gamer_ranks_lightweight_first():
    """The product's core promise: a weight-conscious FPS gamer sees the 60g
    Superlight on top and the 141g MX Master at the bottom."""
    results = recommend(PAYLOADS[_GAMER], MICE)["results"]
    ids = [m["id"] for m in results]
    assert ids[0] == _LIGHTEST, f"expected lightest mouse first, got order {ids}"
    assert ids[-1] == _HEAVIEST, f"expected heaviest mouse last, got order {ids}"
    by_id = {m["id"]: m for m in results}
    assert by_id[_LIGHTEST]["score"] > by_id[_HEAVIEST]["score"]


def test_student_ranks_heavy_last():
    """A student who travels often should be steered away from the heavy mouse."""
    ids = [m["id"] for m in recommend(PAYLOADS[_STUDENT], MICE)["results"]]
    assert ids[-1] == _HEAVIEST, f"expected heaviest mouse last, got order {ids}"


def test_results_sorted_by_score_desc():
    """Whatever the weights, results always come back best-first."""
    for label, payload in PAYLOADS.items():
        scores = [m["score"] for m in recommend(payload, MICE)["results"]]
        assert scores == sorted(scores, reverse=True), f"{label}: {scores} not descending"


def test_every_candidate_survives():
    """Hard rules reorder but never exclude — every mouse in must come back out."""
    for label, payload in PAYLOADS.items():
        ids = {m["id"] for m in recommend(payload, MICE)["results"]}
        assert ids == {1, 2, 3, 4}, f"{label}: dropped a candidate, got {ids}"


def test_result_shape_is_stable():
    """The frontend reads these keys by name; a rename is a breaking change."""
    result = recommend(PAYLOADS[_GAMER], MICE)
    assert isinstance(result["passed_rules"], list)
    assert isinstance(result["failed_rules"], list)
    assert set(result["passed_rules"]).isdisjoint(result["failed_rules"])
    assert result["results"], "expected at least one ranked mouse"
    for m in result["results"]:
        for key in ("id", "product_name", "brand_name", "score", "explanations"):
            assert key in m, f"result missing {key!r}"
        assert isinstance(m["explanations"], dict)


def test_empty_mice_no_crash():
    """No candidates in -> empty lists out, not an exception."""
    assert recommend(PAYLOADS[_STUDENT], []) == {
        "passed_rules": [],
        "failed_rules": [],
        "results": [],
    }


def test_empty_payload_returns_all():
    """No answers -> nothing to fail -> every mouse still returned."""
    ids = {m["id"] for m in recommend({}, MICE)["results"]}
    assert ids == {1, 2, 3, 4}


if __name__ == "__main__":
    _tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for _t in _tests:
        _t()
        print("OK", _t.__name__)
    print("ALL PASSED")