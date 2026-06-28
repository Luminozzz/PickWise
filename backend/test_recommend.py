"""
Quick smoke-test for backend/algorithm/recommend.py.

Run from the backend/ directory:
    python test_recommend.py

Uses mock Mouse objects so no real database is needed.
Budget is intentionally omitted from the payload to skip the
Price_History.query call (which requires a live DB/app context).
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

def _gaming(rgb=False, tracking_speed=400):
    return SimpleNamespace(rgb=rgb, tracking_speed=tracking_speed)

def _mouse(id, product_name, brand_name, *,
           length=120, weight=90, left_fit=False,
           ergonomy=Ergonomy.SYMMETRICAL, max_DPI=8000,
           number_of_buttons=3, min_battery_life=50,
           max_polling_rate=1000, connectivity=None, gaming_specs=None):
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
        max_polling_rate=max_polling_rate,
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


def run_test(label, payload):
    print("=" * 60)
    print(f"  {label}")
    print("=" * 60)
    result = recommend(payload, MICE)
    print(f"Passed hard rules : {result['passed_rules']}")
    print(f"Failed hard rules : {result['failed_rules']}")
    print()
    for m in result["results"]:
        print(f"  [{m['score']:+.1f}]  {m['brand_name']} {m['product_name']}")
        for rule_id, explanation in m["explanations"].items():
            print(f"          {rule_id}: {explanation}")
        print()


if __name__ == "__main__":
    for label, payload in PAYLOADS.items():
        run_test(label, payload)