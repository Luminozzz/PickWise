from database.models import db, Mouse, Gaming_Mouse, Price_History, Mouse_Skins, Hand_Fit, Ergonomy, Connectivity, create_app
from scrapers import *
from extractors import *
import sys

BRAND_EXTRACTORS = {
    #'Razer': (razer_extractor, razer_scraper),
    'Logitech': (logitech_extractor, logitech_scraper)
}

app = create_app()

def seed_all():
    for brand_name, (Extractor_Class, Scraper_Class) in BRAND_EXTRACTORS.items():
        extractor = Extractor_Class()
        scraper = Scraper_Class()
        data = extractor.load_csv(scraper.run())
        existing_names = [name for (name,) in db.session.query(Mouse.product_name).filter_by(brand_name=brand_name).all()]

        for product_name, feature in data.items():
            print(product_name)
            if product_name in existing_names:
                continue
            battery_life = feature['battery_life']
            polling_rate = feature['polling_rate']
            mouse = Mouse(
                product_name = product_name.strip(),
                brand_name = feature['brand_name'],
                link = feature['link'],
                img_link = feature['img_link'],
                ergonomy = Ergonomy(feature['ergonomy']),
                connectivity = Connectivity(feature['connectivity']),
                hand_fit = Hand_Fit(feature['hand_fit']),
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
                other_features = feature['other_features']
            )
            db.session.add(mouse)

            db.session.flush()

            if feature['tracking_speed'] is not None:
                gaming = Gaming_Mouse(
                    mouse_id = mouse.id,
                    acceleration = feature['max_acceleration'],
                    tracking_speed = feature['tracking_speed']
                )
                db.session.add(gaming)
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
        # all_mouses = Mouse.query.all()
        # mice_not_in_price_db = [mouse for mouse in all_mouses if mouse.id not in ids_in_price_db]

        data = ['Logitech G705', 'Logitech PRO X SUPERLIGHT 2', 'Logitech M720 Triathlon']
        # for mouse in mice_not_in_price_db:
        #     data.append(mouse.product_name)
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
                    colour = item['colour'],
                    store_link = item['store_link'],
                    store_name = item['store_name']
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