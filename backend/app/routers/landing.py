from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db

api_router = APIRouter()

@api_router.get("/", response_class=HTMLResponse)
async def landing_page():
    with open("app/templates/page.html") as f:
        return f.read()


# One row per mouse, enriched with connectivity, gaming specs, the cheapest
# current price, the best-reviewed listing, and any colour variants.
_ITEMS_SQL = text(
    """
    SELECT
        m.id, m.product_name, m.brand_name, m.link, m.img_link, m.alt_img_link,
        m.left_fit,
        m.ergonomy, m."max_DPI", m.length, m.width, m.height, m.weight,
        m.number_of_buttons, m.min_battery_life, m.max_battery_life,
        m.other_features,
        c.bluetooth, c.dongle, c.wired,
        g.rgb, g.tracking_speed, g.acceleration, g.max_polling_rate,
        p.price AS price_amount, p.currency AS price_currency, p.date AS price_date,
        r.num_of_stars AS rating_stars, r.num_of_reviews AS rating_reviews,
        sk.colours
    FROM mouse_model m
    LEFT JOIN mouse_connectivity c ON c.mouse_id = m.id
    LEFT JOIN gaming_mouse_specs g ON g.mouse_id = m.id
    LEFT JOIN LATERAL (
        SELECT ph.price, ph.currency, ph.date
        FROM price_history ph
        JOIN mouse_skins sk_p ON sk_p.id = ph.mouse_id
        WHERE sk_p.mouse_id = m.id
        ORDER BY ph.date DESC, ph.price ASC LIMIT 1
    ) p ON true
    LEFT JOIN LATERAL (
        SELECT ph.num_of_stars, ph.num_of_reviews
        FROM price_history ph
        JOIN mouse_skins sk_r ON sk_r.id = ph.mouse_id
        WHERE sk_r.mouse_id = m.id AND ph.num_of_stars IS NOT NULL
        ORDER BY ph.num_of_reviews DESC NULLS LAST LIMIT 1
    ) r ON true
    LEFT JOIN LATERAL (
        SELECT array_agg(DISTINCT colour) AS colours FROM mouse_skins
        WHERE mouse_id = m.id
    ) sk ON true
    ORDER BY m.id
    """
)


@api_router.get("/api/v1/items")
async def get_items(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(_ITEMS_SQL)).mappings().all()
    return [_shape(row) for row in rows]


def _shape(row):
    r = dict(row)

    connectivity = None
    if r["bluetooth"] is not None or r["dongle"] is not None or r["wired"] is not None:
        connectivity = {
            "bluetooth": bool(r["bluetooth"]),
            "dongle": bool(r["dongle"]),
            "wired": bool(r["wired"]),
        }

    gaming = None
    if r["tracking_speed"] is not None or r["acceleration"] is not None or r["rgb"] is not None:
        gaming = {
            "rgb": r["rgb"],
            "tracking_speed": r["tracking_speed"],
            "acceleration": r["acceleration"],
            "max_polling_rate": r["max_polling_rate"],
        }

    price = None
    if r["price_amount"] is not None:
        price = {
            "amount": r["price_amount"],
            "currency": r["price_currency"],
            "date": r["price_date"],
        }

    rating = None
    if r["rating_stars"] is not None:
        rating = {"stars": r["rating_stars"], "reviews": r["rating_reviews"]}

    return {
        "id": r["id"],
        "product_name": r["product_name"],
        "brand_name": r["brand_name"],
        "link": r["link"],
        "img_link": r["img_link"],
        "alt_img_link": r["alt_img_link"],
        "left_fit": r["left_fit"],
        "ergonomy": r["ergonomy"],
        "max_DPI": r["max_DPI"],
        "length": r["length"],
        "width": r["width"],
        "height": r["height"],
        "weight": r["weight"],
        "number_of_buttons": r["number_of_buttons"],
        "min_battery_life": r["min_battery_life"],
        "max_battery_life": r["max_battery_life"],
        "max_polling_rate": r["max_polling_rate"],
        "other_features": r["other_features"],
        "connectivity": connectivity,
        "gaming": gaming,
        "price": price,
        "rating": rating,
        "colours": r["colours"] or [],
    }
