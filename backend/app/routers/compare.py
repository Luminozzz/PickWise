"""Side-by-side comparison: the same spec rows for every compared mouse, ordered
by what matters most to this user — or a sensible default when they haven't taken
the quiz. Plain ORM queries, mirroring product.py, so it works on the SQLite
snapshot too."""
from fastapi import APIRouter, Body, HTTPException
from sqlalchemy.orm import joinedload

from algorithm.recommend import build_facts, compare_detail
from app.routers.product import _description
from app.routers.recommend import build_payload
from database.models import SessionLocal, Mouse, Price_History

api_router = APIRouter()

# Desktop shows at most three columns; the client clamps to two on narrow
# screens. Capping here as well keeps a hand-typed /compare/1-2-3-4-5 honest.
MAX_COMPARE = 3


def _clean_ids(raw) -> list:
    """Positive ints only, de-duplicated, caller's order preserved, capped.

    Junk is dropped before the cap, not after: otherwise ids like 0 or -1 would
    eat the three slots and silently hide real products behind them.
    """
    ids = []
    for value in raw or []:
        try:
            i = int(value)
        except (TypeError, ValueError):
            continue
        if i > 0 and i not in ids:
            ids.append(i)
    return ids[:MAX_COMPARE]


@api_router.post("/api/v1/compare")
def compare_route(body: dict = Body(default=None)):
    body = body or {}
    ids = _clean_ids(body.get("ids"))
    answers = body.get("answers") or {}

    if not ids:
        return {"has_answers": bool(answers), "products": [], "rows": []}

    with SessionLocal() as session:
        found = (
            session.query(Mouse)
            .options(joinedload(Mouse.connectivity), joinedload(Mouse.gaming_specs))
            .filter(Mouse.id.in_(ids))
            .all()
        )
        by_id = {m.id: m for m in found}
        # Keep the caller's column order; ignore ids that no longer exist.
        mice = [by_id[i] for i in ids if i in by_id]
        if not mice:
            raise HTTPException(status_code=404, detail="no products found")

        # Every compared mouse needs its own price in facts: _spec_price and the
        # budget rule both look up prices[mouse.id], so a single-mouse dict would
        # blank the price row for every column but one.
        prices = {}
        currency = None
        ratings = {}
        for mouse in mice:
            price_row = (
                session.query(Price_History)
                .filter_by(mouse_id=mouse.id)
                .order_by(Price_History.date.desc(), Price_History.price.asc())
                .first()
            )
            if price_row is not None:
                prices[mouse.id] = price_row.price
                currency = currency or price_row.currency

            rating_row = (
                session.query(Price_History)
                .filter(
                    Price_History.mouse_id == mouse.id,
                    Price_History.num_of_stars.isnot(None),
                )
                .order_by(Price_History.num_of_reviews.desc())
                .first()
            )
            if rating_row is not None:
                ratings[mouse.id] = rating_row

        payload = build_payload(answers)
        payload["prices"] = prices
        facts = build_facts(payload)
        facts["currency"] = currency

        products = []
        for mouse in mice:
            rating = ratings.get(mouse.id)
            products.append({
                "id": mouse.id,
                "product_name": mouse.product_name,
                "brand_name": mouse.brand_name,
                "link": mouse.link,
                "img_link": mouse.img_link,
                "description": _description(mouse),
                "price": prices.get(mouse.id),
                "currency": currency,
                "rating": (
                    {"stars": rating.num_of_stars, "reviews": rating.num_of_reviews}
                    if rating is not None else None
                ),
            })

        return {
            "has_answers": bool(answers),
            "products": products,
            "rows": compare_detail(mice, facts),
        }
