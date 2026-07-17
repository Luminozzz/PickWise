"""Single-product detail: full specs ordered by importance to the user, each
tagged fit/unfit/neutral against their questionnaire answers (or unjudged when
there are none). Plain ORM queries, so it works on the SQLite snapshot too."""
import re

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


def _norm_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).strip()


def _same_family(a: str, b: str) -> bool:
    """True when two names are editions of the same mouse.

    The catalogue carries many colourways/editions of one model ("Viper V3 Pro",
    "... SE", "... Faker Edition"). They score as near-identical, so without this
    the section would just list the same mouse three times instead of offering
    real alternatives.
    """
    x, y = _norm_name(a), _norm_name(b)
    if not x or not y:
        return False
    return x.startswith(y) or y.startswith(x)


def _conn_kind(mouse) -> str | None:
    conn = mouse.connectivity
    if conn is None:
        return None
    wireless = bool(conn.bluetooth or conn.dongle)
    wired = bool(conn.wired)
    if wireless and wired:
        return "wired + wireless"
    if wireless:
        return "wireless"
    if wired:
        return "wired"
    return None


def _ergonomy_label(mouse) -> str | None:
    e = mouse.ergonomy
    if e is None:
        return None
    val = e.value if hasattr(e, "value") else str(e)
    return None if val in ("none", "NOT_MENTIONED") else val


def _closeness(a, b, tol):
    """1.0 when equal, fading to 0.0 once `tol` apart. None when either is unknown."""
    if a is None or b is None or not tol:
        return None
    return max(0.0, 1.0 - abs(float(a) - float(b)) / float(tol))


def _similarity(base, cand, base_price, cand_price):
    """Score `cand` against `base` and explain the match.

    Each dimension contributes weight * closeness to a normalised score; any
    dimension that lands a strong match doubles as a human-readable reason, so
    the card can say *why* it's similar rather than just asserting it.
    """
    dims = []  # (weight, closeness, reason)

    bk, ck = _conn_kind(base), _conn_kind(cand)
    if bk and ck:
        dims.append((2.5, 1.0 if bk == ck else 0.0, f"Also {ck}"))

    w = _closeness(base.weight, cand.weight, 25.0)
    if w is not None:
        dims.append((2.0, w, f"Similar weight — {cand.weight:g} g"))

    if base_price and cand_price:
        p = _closeness(base_price, cand_price, max(float(base_price) * 0.35, 10.0))
        dims.append((1.8, p, "Similar price"))

    be, ce = _ergonomy_label(base), _ergonomy_label(cand)
    if be and ce:
        dims.append((1.5, 1.0 if be == ce else 0.0, f"Same shape — {ce}"))

    d = _closeness(base.max_DPI, cand.max_DPI, max((base.max_DPI or 0) * 0.5, 4000))
    if d is not None:
        dims.append((1.0, d, f"Similar sensor — {cand.max_DPI:,} DPI"))

    s = _closeness(base.length, cand.length, 15.0)
    if s is not None:
        dims.append((1.0, s, "Similar size"))

    b = _closeness(base.number_of_buttons, cand.number_of_buttons, 4.0)
    if b is not None:
        dims.append((0.9, b, f"{cand.number_of_buttons} buttons, like this one"))

    if base.brand_name and cand.brand_name:
        same = base.brand_name == cand.brand_name
        dims.append((0.6, 1.0 if same else 0.0, f"Same brand — {cand.brand_name}"))

    if base.gaming_specs is not None and cand.gaming_specs is not None:
        dims.append((0.5, 1.0, "Both gaming mice"))

    total = sum(wt for wt, _, _ in dims)
    if not total:
        return 0.0, []
    score = sum(wt * cl for wt, cl, _ in dims) / total

    # Strongest matches first; a weak/failed dimension never becomes a reason.
    ranked = sorted(dims, key=lambda t: t[0] * t[1], reverse=True)
    reasons = [r for wt, cl, r in ranked if cl >= 0.6]
    return score, reasons[:3]


def _similar_products(session, base, base_price, limit=3):
    """The `limit` most similar mice to `base`, each with its reasons."""
    candidates = (
        session.query(Mouse)
        .options(joinedload(Mouse.connectivity), joinedload(Mouse.gaming_specs))
        .filter(Mouse.id != base.id)
        .all()
    )

    # Cheapest price on the most recent date, per mouse — mirrors the catalogue.
    price_by_mouse = {}
    for row in (
        session.query(Price_History)
        .order_by(Price_History.date.desc(), Price_History.price.asc())
        .all()
    ):
        price_by_mouse.setdefault(row.mouse_id, row)

    rating_by_mouse = {}
    for row in (
        session.query(Price_History)
        .filter(Price_History.num_of_stars.isnot(None))
        .order_by(Price_History.num_of_reviews.desc())
        .all()
    ):
        rating_by_mouse.setdefault(row.mouse_id, row)

    scored = []
    for cand in candidates:
        cand_price_row = price_by_mouse.get(cand.id)
        score, reasons = _similarity(
            base, cand, base_price, cand_price_row.price if cand_price_row else None
        )
        # Only surface a mouse we can actually justify showing.
        if reasons:
            scored.append((score, cand, reasons))

    scored.sort(key=lambda s: s[0], reverse=True)

    # One pick per model family, and never another edition of the mouse being
    # viewed — three colourways of the same mouse aren't "similar products".
    top = []
    for entry in scored:
        cand = entry[1]
        if _same_family(base.product_name, cand.product_name):
            continue
        if any(_same_family(c.product_name, cand.product_name) for _, c, _ in top):
            continue
        top.append(entry)
        if len(top) == limit:
            break

    colours_by_mouse = {}
    if top:
        ids = [c.id for _, c, _ in top]
        for mid, colour in (
            session.query(Mouse_Skins.mouse_id, Mouse_Skins.colour)
            .filter(Mouse_Skins.mouse_id.in_(ids))
            .distinct()
            .all()
        ):
            colours_by_mouse.setdefault(mid, []).append(colour)

    out = []
    for _, cand, reasons in top:
        price_row = price_by_mouse.get(cand.id)
        rating_row = rating_by_mouse.get(cand.id)
        conn = cand.connectivity
        out.append({
            "id": cand.id,
            "product_name": cand.product_name,
            "brand_name": cand.brand_name,
            "link": cand.link,
            "img_link": cand.img_link,
            "weight": cand.weight,
            "max_DPI": cand.max_DPI,
            "number_of_buttons": cand.number_of_buttons,
            "max_polling_rate": cand.max_polling_rate,
            "max_battery_life": cand.max_battery_life,
            "connectivity": (
                {"bluetooth": conn.bluetooth, "dongle": conn.dongle, "wired": conn.wired}
                if conn is not None else None
            ),
            "price": (
                {"amount": price_row.price, "currency": price_row.currency}
                if price_row is not None else None
            ),
            "rating": (
                {"stars": rating_row.num_of_stars, "reviews": rating_row.num_of_reviews}
                if rating_row is not None else None
            ),
            "colours": colours_by_mouse.get(cand.id, []),
            "reasons": reasons,
        })
    return out


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
            "similar": _similar_products(session, mouse, price),
        }
