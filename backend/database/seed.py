from database.models import db, Mouse, Gaming_Mouse, Mouse_Connectivity, Sort_By, Price_History, Mouse_Skins, Ergonomy, create_app
from scrapers import *
import sys
from database import config
import re

BRAND_EXTRACTORS = {
    #'Razer': razer_scraper,
    'Logitech': logitech_scraper
}

OFFICIAL_STORE = {
    'Razer': (razer_price_scraper)
}

app = create_app()

def seed_all():
    for brand_name, Scraper_Class in BRAND_EXTRACTORS.items():
        scraper = Scraper_Class()
        data = scraper.run()
        existing = {
            m.product_name: m
            for m in db.session.query(Mouse).filter_by(brand_name=brand_name).all()
        }

        for product_name, feature in data.items():
            print(product_name)
            name = product_name.strip()
            battery_life = feature['battery_life']
            polling_rate = feature['polling_rate']
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
                min_polling_rate = polling_rate[0],
                max_polling_rate = polling_rate[1],
                other_features = feature['other_features'],
            )

            mouse = existing.get(name)

            if mouse is not None:
                for key, value in mouse_fields.items():
                    setattr(mouse, key, value)
            
            else:
                mouse = Mouse(**mouse_fields)
                db.session.add(mouse)
                db.session.flush()

            connectivity = db.session.query(Mouse_Connectivity).filter_by(mouse_id=mouse.id).first()

            if connectivity is None:
                connectivity = Mouse_Connectivity(mouse_id=mouse.id)
                db.session.add(connectivity)

            connectivity.bluetooth = feature['bluetooth']
            connectivity.dongle = feature['dongle']
            connectivity.wired = feature['wired']
            
            gaming = db.session.query(Gaming_Mouse).filter_by(mouse_id=mouse.id).first()
            if feature['tracking_speed'] is not None or feature['max_acceleration'] is not None:
                if gaming is None:
                    gaming = Gaming_Mouse(mouse_id=mouse.id)
                    db.session.add(gaming)
                gaming.rgb = feature['rgb']
                gaming.acceleration = feature['max_acceleration']
                gaming.tracking_speed = feature['tracking_speed']

    db.session.commit()

def add_mouse_skins():
    with app.app_context():
        db.create_all()
        razer_mouses = Mouse.query.filter_by(brand_name="Razer").all()
        data = []
        for mouse in razer_mouses:
            data.append({'product_name': mouse.product_name, 'link': mouse.link})
        scraper = razer_skin_scraper()
        revised_data = scraper.run(data)
        for item in revised_data:
            exists = Mouse_Skins.query.filter_by(product_name=item['product_name']).first()
            mouse = Mouse.query.filter_by(product_name=item['product_name']).first()
            if mouse and not exists:
                skin = Mouse_Skins(
                    mouse_id = mouse.id,
                    product_name = item['product_name'],
                    colour = item['colour'],
                    img_link = item['img_link']
                )
                db.session.add(skin)
        db.session.commit()

def add_new_product_price():
    with app.app_context():
        db.create_all()
        # ids_in_price_db = db.session.query(Price_History.mouse_id).distinct().all()
        # ids_in_price_db = [row[0] for row in ids_in_price_db]
        all_mouses = Mouse.query.all()
        #mouses = [mouse[0] for mouse in all_mouses]
        #mice_not_in_price_db = [mouse for mouse in all_mouses if mouse.id not in ids_in_price_db]
        data = []
       
        for mouse in all_mouses:
            data.append(mouse.product_name)
        scraper = amazon_new_product_price_scraper()
        revised_data = scraper.run(data)
        for item in revised_data:
            mouse = Mouse.query.filter_by(product_name=item['product_name']).first()
            if mouse:
                price = Price_History(
                    mouse_id = mouse.id,
                    product_name = item['product_name'],
                    date = item['date'],
                    currency = item['currency'],
                    price = item['price'],
                    num_of_stars = item['num_of_stars'],
                    num_of_reviews = item['num_of_reviews'],
                    colour = item['colour'],
                    store_link = item['store_link'],
                    store_name = item['store_name'],
                    sort_by = Sort_By(item['sort_by'])
                )
                db.session.add(price)
        db.session.commit()

def add_official_store_product_price():
    for brand_name, price_scraper in OFFICIAL_STORE.items():
        scraper = price_scraper()
        with app.app_context():
            db.create_all()
            data = []
            lst_of_mouse_filtered_brand = Mouse.query.filter_by(brand_name = 'Razer').all()

            for mouse in lst_of_mouse_filtered_brand:
                mouses = Mouse_Skins.query.filter_by(product_name = mouse.product_name).all()
                colours = [mouse.colour for mouse in mouses]
                if colours:
                    for colour in colours:
                        data.append({
                            'product_name': mouse.product_name,
                            'link': mouse.link,
                            'colour': colour
                        })
                else:
                    data.append({
                            'product_name': mouse.product_name,
                            'link': mouse.link,
                            'colour': None
                        })
            revised_data = scraper.run(data)

            for p in revised_data:
                mouse = Mouse.query.filter_by(product_name=p['product_name']).first()
                if mouse:
                    price = Price_History(
                        mouse_id = mouse.id,
                        product_name = p['product_name'],
                        date = p['date'],
                        currency = p['currency'],
                        price = p['price'],
                        num_of_stars = p['num_of_stars'],
                        num_of_reviews = p['num_of_reviews'],
                        colour = p['colour'],
                        store_link = p['store_link'],
                        store_name = p['store_name'],
                        sort_by = Sort_By(p['sort_by'])
                    )
                    db.session.add(price)
            db.session.commit()

if __name__ == "__main__":
    if sys.argv[1] == 'seed_all':
        with app.app_context():
            db.create_all()
            seed_all()
    if sys.argv[1] == 'add_mouse_skins':
        add_mouse_skins()
    if sys.argv[1] == 'add_new_product_price':
        add_new_product_price()
    if sys.argv[1] == 'add_official_store_product_price':
        add_official_store_product_price()