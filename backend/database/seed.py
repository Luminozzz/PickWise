import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from database.models import (
    Mouse,
    Gaming_Mouse,
    Mouse_Connectivity,
    Sort_By,
    Price_History,
    Mouse_Skins,
    Ergonomy,
    init_db,
    SessionLocal,
)
from scrapers import *
from scrapers.image_utils import razer_primary_render
from sqlalchemy.dialects.postgresql import insert as pg_insert
import sys

BRAND_EXTRACTORS = {
    'Razer': razer_scraper,
    'Logitech': logitech_scraper,
    'HP': hp_scraper,
    'UGreen': ugreen_scraper,
    'Asus': asus_scraper,
}

OFFICIAL_STORE = {
    'Razer': (razer_price_scraper)
}

session = SessionLocal()

def seed_all(brands=None):
    """brands: optional iterable of BRAND_EXTRACTORS keys to limit this run
    to (e.g. ['HP']) - defaults to every registered brand."""
    for brand_name, Scraper_Class in BRAND_EXTRACTORS.items():
        if brands is not None and brand_name not in brands:
            continue
        scraper = Scraper_Class()
        data = scraper.run()
        # Not filtered by brand_name: HP's own listing includes other
        # manufacturers' products (e.g. HyperX), whose actual brand_name
        # differs from the BRAND_EXTRACTORS key they were scraped under -
        # product_name is globally unique, so matching on it alone is both
        # sufficient and correct for every brand.
        existing = {
            m.product_name: m
            for m in session.query(Mouse).all()
        }

        for product_name, feature in data.items():
            print(product_name)
            name = product_name.strip()
            battery_life = feature['battery_life']
            # .get(), not [] - some brands (e.g. HP) never report a polling
            # rate at all and leave this key as None rather than a fake
            # tuple, so it must be safe to be absent too.
            polling_rate = feature.get('polling_rate')
            mouse_fields = dict(
                product_name = name,
                brand_name = feature['brand_name'],
                link = feature['link'],
                img_link = feature['img_link'],
                ergonomy = Ergonomy(feature['ergonomy']),
                left_fit = feature['left_fit'],
                max_DPI = feature['max_DPI'],
                weight = feature['weight'],
                length = feature['length'],
                width = feature['width'],
                height = feature['height'],
                number_of_buttons = feature['number_of_buttons'],
                min_battery_life = battery_life[0],
                max_battery_life = battery_life[1],
                other_features = feature['other_features'],
            )

            mouse = existing.get(name)

            if mouse is not None:
                for key, value in mouse_fields.items():
                    setattr(mouse, key, value)

            else:
                mouse = Mouse(**mouse_fields)
                session.add(mouse)
                session.flush()

            connectivity = session.query(Mouse_Connectivity).filter_by(mouse_id=mouse.id).first()

            if connectivity is None:
                connectivity = Mouse_Connectivity(mouse_id=mouse.id)
                session.add(connectivity)

            connectivity.bluetooth = feature['bluetooth']
            connectivity.dongle = feature['dongle']
            connectivity.wired = feature['wired']
            # Every mouse is at least wired: default when nothing was detected.
            if not (connectivity.bluetooth or connectivity.dongle or connectivity.wired):
                connectivity.wired = True

            gaming = session.query(Gaming_Mouse).filter_by(mouse_id=mouse.id).first()
            # Polling rate lives here now, so a mouse with a polling rate but no
            # tracking/acceleration still needs a gaming_specs row.
            if (feature['tracking_speed'] is not None
                    or feature['max_acceleration'] is not None
                    or polling_rate[1] is not None):
                if gaming is None:
                    gaming = Gaming_Mouse(mouse_id=mouse.id)
                    session.add(gaming)
                gaming.rgb = feature['rgb']
                gaming.acceleration = feature['max_acceleration']
                gaming.tracking_speed = feature['tracking_speed']
                gaming.max_polling_rate = polling_rate[1] if polling_rate else None

            # Every mouse needs at least one Mouse_Skins row - Price_History
            # attaches to a specific skin now, not the mouse directly.
            colours = feature.get('colours') or [{'Default': feature['img_link']}]
            _sync_mouse_skins(mouse, name, colours)

    session.commit()

def _sync_mouse_skins(mouse, product_name, colours):
    """Insert/update Mouse_Skins rows from a mouse's scraped `colours` list
    (each element is {colour_name: img_url_or_list_of_urls}). Mouse_Skins.img_link
    is a JSON column holding a list of image URLs for that colour - a bare
    string (e.g. Razer's single-render colours) is normalised to a 1-item list."""
    existing_skins = {
        s.colour: s
        for s in session.query(Mouse_Skins).filter_by(mouse_id=mouse.id).all()
    }
    for colour_dict in colours:
        for colour_name, img_link in colour_dict.items():
            colour_name = colour_name.strip()
            # Capitalise just the first letter - a blunt .title()/.capitalize()
            # would mangle names like "NiKo Edition" or "BLACKPINK Edition".
            colour_name = colour_name[:1].upper() + colour_name[1:]
            if not isinstance(img_link, list):
                img_link = [img_link] if img_link else []
            if not img_link:
                continue
            skin = existing_skins.get(colour_name)
            if skin is None:
                # No distinct per-colour buy link is known at this point
                # (only add_mouse_buy_links, Razer-only, scrapes those) - use
                # the mouse's own link until/unless that overwrites it.
                session.add(Mouse_Skins(
                    mouse_id = mouse.id,
                    product_name = product_name,
                    colour = colour_name,
                    img_link = img_link,
                    buy_link = mouse.link,
                ))
            else:
                skin.img_link = img_link

def _sync_mouse_buy_links(mouse, product_name, colour_details):
    """Merge (colour, buy_link, img_link) triples scraped straight off a
    mouse's own product page (razer_skin_scraper) into its Mouse_Skins rows.
    Updates buy_link on colours we already know about and adds any the
    store listing never surfaced as their own card (e.g. collab editions)
    - without touching an existing skin's fuller image gallery. A mouse
    left with only one colour has that skin's buy_link forced back to
    mouse.link - there's nothing to distinguish it by, and the Amazon price
    scraper skips appending colour to its search text when a skin's
    buy_link equals its mouse's own link."""
    existing_skins = {
        s.colour: s
        for s in session.query(Mouse_Skins).filter_by(mouse_id=mouse.id).all()
    }
    for colour_name, buy_link, img_link in colour_details:
        colour_name = colour_name.strip()
        colour_name = colour_name[:1].upper() + colour_name[1:]
        skin = existing_skins.get(colour_name)
        if skin is None:
            skin = Mouse_Skins(
                mouse_id=mouse.id,
                product_name=product_name,
                colour=colour_name,
                img_link=[img_link] if img_link else [],
                buy_link=buy_link,
            )
            session.add(skin)
            existing_skins[colour_name] = skin
        else:
            skin.buy_link = buy_link

    if len(existing_skins) == 1:
        next(iter(existing_skins.values())).buy_link = mouse.link

def add_mouse_buy_links():
    """Backfill each Razer mouse's per-colour buy link by clicking through
    every colour swatch on the mouse's own product page - catches
    colour/edition variants (e.g. collab editions) the cheaper store
    listing scrape in add_mouse_skins() never surfaces as their own card."""
    init_db()
    razer_mouses = {
        m.product_name: m
        for m in session.query(Mouse).filter_by(brand_name="Razer").all()
    }
    lst_of_mouse = [{'product_name': name, 'link': m.link} for name, m in razer_mouses.items()]

    scraper = razer_skin_scraper()
    colour_details = scraper.run(lst_of_mouse)

    grouped = {}
    for item in colour_details:
        grouped.setdefault(item['product_name'], []).append(
            (item['colour'], item['buy_link'], item['img_link'])
        )

    for product_name, mouse in razer_mouses.items():
        details = grouped.get(product_name)
        if details:
            _sync_mouse_buy_links(mouse, product_name, details)
        else:
            # No colour selector found on the product page - only safe to
            # assume single-colour (and thus fall back to mouse.link) if
            # that already matches what we have; otherwise leave it for a
            # retry rather than guessing at colour-specific links we
            # couldn't scrape.
            skins = session.query(Mouse_Skins).filter_by(mouse_id=mouse.id).all()
            if len(skins) == 1:
                skins[0].buy_link = mouse.link

    session.commit()

def add_mouse_skins():
    """Refresh Razer colour variants (Mouse_Skins) straight from the store
    listing page, and prefer a skin's clean transparent render as each
    mouse's main image (covers mice with no colour variants via the
    product page's own PRIMARY render)."""
    init_db()
    scraper = razer_scraper()
    mouse_links = scraper.scrape_razer_store_products()
    razer_mouses = {
        m.product_name: m
        for m in session.query(Mouse).filter_by(brand_name="Razer").all()
    }
    for product_name, info in mouse_links.items():
        mouse = razer_mouses.get(product_name)
        if mouse is None:
            continue
        # Mice with no colour selector on the store page only ship in one
        # colour - default that to "Default" using the mouse's own image.
        colours = info.get('colours') or [{'Default': mouse.img_link}]
        _sync_mouse_skins(mouse, product_name, colours)
    session.flush()

    for mouse in razer_mouses.values():
        skin = session.query(Mouse_Skins).filter_by(mouse_id=mouse.id).order_by(Mouse_Skins.id).first()
        render = skin.img_link[0] if (skin and skin.img_link) else razer_primary_render(mouse.link)
        if render and mouse.img_link != render:
            if not mouse.alt_img_link:
                mouse.alt_img_link = mouse.img_link
            mouse.img_link = render

    session.commit()

def _skin_lookup(skins):
    """(product_name, colour) -> skin id, plus product_name -> default skin id
    (its earliest/first skin, used when a scraped colour is missing or
    doesn't match any known skin)."""
    by_colour = {}
    default_skin = {}
    for skin in skins:
        by_colour[(skin.product_name, skin.colour)] = skin.id
        default_skin.setdefault(skin.product_name, skin.id)
    return by_colour, default_skin

def add_new_product_price():
    init_db()

    read_session = SessionLocal()
    try:
        # Joined to Mouse.link so a skin with no distinct buy link of its
        # own (buy_link == mouse.link) can be told apart from one that has
        # a real, scraped colour-specific link.
        skins = (
            read_session.query(
                Mouse_Skins.id, Mouse_Skins.product_name, Mouse_Skins.colour,
                Mouse_Skins.buy_link, Mouse.link.label('mouse_link'),
            )
            .join(Mouse, Mouse.id == Mouse_Skins.mouse_id)
            .order_by(Mouse_Skins.id)
            .all()
        )
    finally:
        read_session.close()

    # Search Amazon per (product_name, colour) skin rather than once per mouse,
    # so each colour variant gets its own price instead of sharing one.
    # is_default means this mouse only ships in one colour (no distinct
    # buy link of its own), so the scraper leaves colour out of the search
    # text instead of searching on a colour name that's arbitrary/unconfirmed.
    product_colours = [
        {
            'skin_id': s.id,
            'product_name': s.product_name,
            'colour': s.colour,
            'buy_link': s.buy_link,
            'is_default': s.buy_link == s.mouse_link,
        }
        for s in skins
    ]
    skin_by_colour, default_skin = _skin_lookup(skins)

    scraper = amazon_new_product_price_scraper()
    revised_data = scraper.run(product_colours)

    seen = {}
    for item in revised_data:
        # Prefer the skin_id carried through from the searched skin; fall back
        # to a colour/name match for variants discovered on the product page
        # that we didn't explicitly search for.
        skin_id = item.get('skin_id') or skin_by_colour.get((item['product_name'], item['colour'])) or default_skin.get(item['product_name'])
        if skin_id is None:
            continue
        key = (skin_id, item['store_name'], item['date'], item['sort_by'])
        seen[key] = {
            'mouse_id': skin_id,
            'product_name': item['product_name'],
            'date': item['date'],
            'currency': item['currency'],
            'price': item['price'],
            'num_of_stars': item['num_of_stars'],
            'num_of_reviews': item['num_of_reviews'],
            'store_link': item['store_link'],
            'store_name': item['store_name'],
            'sort_by': Sort_By(item['sort_by']),
        }

    write_session = SessionLocal()
    try:
        for row in seen.values():
            stmt = pg_insert(Price_History).values([row])
            stmt = stmt.on_conflict_do_update(
                constraint='uq_price_history_mouse_store_date',
                set_={
                    'price': stmt.excluded.price,
                    'num_of_stars': stmt.excluded.num_of_stars,
                    'num_of_reviews': stmt.excluded.num_of_reviews,
                    'store_link': stmt.excluded.store_link,
                    'currency': stmt.excluded.currency,
                }
            )
            write_session.execute(stmt)
        write_session.commit()
    except Exception:
        write_session.rollback()
        raise
    finally:
        write_session.close()

def add_official_store_product_price():
    for brand_name, price_scraper in OFFICIAL_STORE.items():
        scraper = price_scraper()
        init_db()
        data = []
        skin_lookup = {}  # (product_name, colour) -> skin id
        lst_of_mouse_filtered_brand = session.query(Mouse).filter_by(brand_name='Razer').all()

        for mouse in lst_of_mouse_filtered_brand:
            skins = session.query(Mouse_Skins).filter_by(mouse_id=mouse.id).order_by(Mouse_Skins.id).all()
            for skin in skins:
                data.append({
                    'product_name': mouse.product_name,
                    'link': mouse.link,
                    'colour': skin.colour,
                })
                skin_lookup[(mouse.product_name, skin.colour)] = skin.id
        revised_data = scraper.run(data)

        rows = []
        for p in revised_data:
            skin_id = skin_lookup.get((p['product_name'], p['colour']))
            if skin_id is None:
                continue
            rows.append({
                'mouse_id': skin_id,
                'product_name': p['product_name'],
                'date': p['date'],
                'currency': p['currency'],
                'price': p['price'],
                'num_of_stars': p['num_of_stars'],
                'num_of_reviews': p['num_of_reviews'],
                'store_link': p['store_link'],
                'store_name': p['store_name'],
                'sort_by': Sort_By(p['sort_by']),
            })
        if rows:
            stmt = pg_insert(Price_History).values(rows)
            stmt = stmt.on_conflict_do_update(
                constraint='uq_price_history_mouse_store_date',
                set_={
                    'price': stmt.excluded.price,
                    'num_of_stars': stmt.excluded.num_of_stars,
                    'num_of_reviews': stmt.excluded.num_of_reviews,
                    'store_link': stmt.excluded.store_link,
                    'currency': stmt.excluded.currency,
                }
            )
            session.execute(stmt)
        session.commit()

if __name__ == "__main__":
    if sys.argv[1] == 'seed_all':
        init_db()
        # Extra argv entries restrict this run to specific BRAND_EXTRACTORS
        # keys, e.g. `seed_all HP` - omit them to seed every brand.
        seed_all(brands=sys.argv[2:] or None)
    if sys.argv[1] == 'add_mouse_skins':
        add_mouse_skins()
    if sys.argv[1] == 'add_mouse_buy_links':
        add_mouse_buy_links()
    if sys.argv[1] == 'add_new_product_price':
        add_new_product_price()
    if sys.argv[1] == 'add_official_store_product_price':
        add_official_store_product_price()
