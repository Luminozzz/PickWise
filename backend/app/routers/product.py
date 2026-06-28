"""Single-product detail: full specs ordered by importance to the user, each
tagged fit/unfit/neutral against their questionnaire answers (or unjudged when
there are none). Plain ORM queries, so it works on the SQLite snapshot too."""
from fastapi import APIRouter, Body, HTTPException
from sqlalchemy.orm import joinedload

from algorithm.recommend import build_facts, product_detail
from app.routers.recommend import build_payload
from database.models import SessionLocal, Mouse, Mouse_Skins, Price_History

api_router = APIRouter()


def _description(mouse) -> str:
    conn = mouse.connectivity
    parts = []
    if conn is not None:
        wireless = bool(conn.bluetooth or conn.dongle)
        wired = bool(conn.wired)
        if wireless and wired:
            parts.append("Wired + wireless")
        elif wireless:
            parts.append("Wireless")
        elif wired:
            parts.append("Wired")
    parts.append("gaming mouse" if mouse.gaming_specs is not None else "mouse")
    sentence = " ".join(parts)
    return sentence[0].upper() + sentence[1:] if sentence else "Mouse"


@api_router.post("/api/v1/product/{mouse_id}")
def product_route(mouse_id: int, answers: dict = Body(default=None)):
    with SessionLocal() as session:
        mouse = (
            session.query(Mouse)
            .options(joinedload(Mouse.connectivity), joinedload(Mouse.gaming_specs))
            .filter_by(id=mouse_id)
            .first()
        )
        if mouse is None:
            raise HTTPException(status_code=404, detail="product not found")

        colours = [
            c for (c,) in session.query(Mouse_Skins.colour)
            .filter_by(mouse_id=mouse_id)
            .distinct()
            .all()
        ]

        price_row = (
            session.query(Price_History)
            .filter_by(mouse_id=mouse_id)
            .order_by(Price_History.date.desc(), Price_History.price.asc())
            .first()
        )
        rating_row = (
            session.query(Price_History)
            .filter(Price_History.mouse_id == mouse_id, Price_History.num_of_stars.isnot(None))
            .order_by(Price_History.num_of_reviews.desc())
            .first()
        )

        price = price_row.price if price_row else None
        currency = price_row.currency if price_row else None

        payload = build_payload(answers or {})
        payload["prices"] = {mouse_id: price} if price is not None else {}
        facts = build_facts(payload)
        facts["currency"] = currency

        detail = product_detail(mouse, facts)

        conn = mouse.connectivity
        return {
            "id": mouse.id,
            "product_name": mouse.product_name,
            "brand_name": mouse.brand_name,
            "link": mouse.link,
            "img_link": mouse.img_link,
            "alt_img_link": mouse.alt_img_link,
            "description": _description(mouse),
            "price": price,
            "currency": currency,
            "rating": (
                {"stars": rating_row.num_of_stars, "reviews": rating_row.num_of_reviews}
                if rating_row else None
            ),
            "colours": colours,
            "connectivity": (
                {"bluetooth": conn.bluetooth, "dongle": conn.dongle, "wired": conn.wired}
                if conn is not None else None
            ),
            "details": detail["details"],
            "criteria": detail["criteria"],
            "has_answers": bool(answers),
        }
