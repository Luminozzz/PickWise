"""Round-trip tests for the preference profile model + routes.
Run from backend/:  python test_profile.py
Uses a throwaway SQLite DB so the real mouse.db is never touched.
"""
import os, sys, tempfile

# Isolate the DB BEFORE importing models (the engine is built at import time).
_TMP_DB = os.path.join(tempfile.gettempdir(), "lumino_test_profile.db")
if os.path.exists(_TMP_DB):
    os.remove(_TMP_DB)
os.environ["DATABASE_URL"] = "sqlite:///" + _TMP_DB

# Same import roots the algorithm/app code expects.
BACKEND = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND)
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, BACKEND)

from database.models import Preference_Profile, SessionLocal, init_db


def test_model_round_trip():
    init_db()
    with SessionLocal() as s:
        prof = Preference_Profile(id="abc-123", answers={"1": "gamer", "17": {"min": 20, "max": 150}})
        s.add(prof)
        s.commit()
    with SessionLocal() as s:
        loaded = s.get(Preference_Profile, "abc-123")
        assert loaded is not None
        assert loaded.answers["1"] == "gamer"
        assert loaded.answers["17"] == {"min": 20, "max": 150}
    print("OK test_model_round_trip")


if __name__ == "__main__":
    test_model_round_trip()
    print("ALL PASSED")
