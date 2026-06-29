"""Recommendation route: questionnaire answers -> scoring algorithm -> ranked mice."""
from fastapi import APIRouter, Body
from sqlalchemy import text
from sqlalchemy.orm import joinedload

from algorithm.recommend import recommend
from database.models import SessionLocal, Mouse

api_router = APIRouter()


# --- questionnaire answer -> algorithm payload --------------------------------

_USAGE_FROM_FREQ = {
    "daily": "most_of_the_time",
    "weekly": "often",
    "occasionally": "occasionally",
    "rarely": "rarely",
    "never": "never",
}


def _hours_to_usage(hours):
    """Bucket a 0-24h slider value into the Usage enum the office rule expects."""
    if hours is None:
        return None
    h = float(hours)
    if h >= 8:
        return "most_of_the_time"
    if h >= 6:
        return "often"
    if h >= 4:
        return "occasionally"
    if h >= 2:
        return "rarely"
    return "never"


def _extra_buttons(value):
    if value is None:
        return None
    return {"yes": "yes", "sometimes": "preferably", "no": "no"}.get(value, value)


def build_payload(answers: dict) -> dict:
    """Map the questionnaire `answers` (keyed by question id) to recommend()'s payload."""
    a = {str(k): v for k, v in (answers or {}).items()}

    def get(qid):
        return a.get(str(qid))

    user_type = get(1)
    if user_type == "office":
        user_type = "office_worker"

    budget = get(17) or {}

    # extra_buttons comes from Q4 (student) or Q9 (office)
    extra = get(4) if get(4) is not None else get(9)

    return {
        "user_type": user_type,
        "hand_size": get(13),
        "wireless": get(15),
        "wired_too": (get(16) == "yes") if get(16) is not None else None,
        "budget_min": budget.get("min") if isinstance(budget, dict) else None,
        "budget_max": budget.get("max") if isinstance(budget, dict) else None,
        # only left-handers need the left-hand constraint; right/either = no filter
        "left_hand": True if get(14) == "left" else None,
        "type_of_game": "none_of_the_above" if get(5) == "other" else get(5),
        "light_weight": (get(6) in ("high", "medium")) if get(6) is not None else None,
        "rgb": (get(7) == "yes") if get(7) is not None else None,
        "travel_portability": _USAGE_FROM_FREQ.get(get(3)),
        "extra_buttons": _extra_buttons(extra),
        "hours_worked": _hours_to_usage(get(11)),
        # collected for future rules (grip / sensitivity / colour / brand)
        "grip_style": get(19),
        "sensitivity": get(20),
        "colour": None if get(21) == "none" else get(21),
        "brand_pref": get(18),
        "value_priority": get(22),
    }


# --- route --------------------------------------------------------------------

@api_router.post("/api/v1/recommend")
def recommend_route(answers: dict = Body(...)):
    payload = build_payload(answers)

    with SessionLocal() as session:
        candidates = (
            session.query(Mouse)
            .options(joinedload(Mouse.connectivity), joinedload(Mouse.gaming_specs))
            .all()
        )

        # one query for every mouse's latest (cheapest) price — the budget rule
        # reads this map instead of hitting the DB per candidate.
        prices = dict(
            session.execute(text(
                """
                SELECT DISTINCT ON (mouse_id) mouse_id, price
                FROM price_history ORDER BY mouse_id, date DESC, price ASC
                """
            )).all()
        )
        payload["prices"] = prices

        result = recommend(payload, candidates)

        by_id = {m.id: m for m in candidates}
        for r in result["results"]:
            m = by_id.get(r["id"])
            if m:
                r["img_link"] = m.img_link
                r["brand_name"] = m.brand_name
                r["price"] = prices.get(m.id)

    return result
