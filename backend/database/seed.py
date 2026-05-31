from database.mouse import Mouse, Gaming_Mouse, Hand_Fit, Ergonomy, Connectivity, create_session
from scrapers import *
from extractors import *

BRAND_EXTRACTORS = {
    #'Razer': (razer_extractor, razer_scraper),
    'Logitech': (logitech_extractor, logitech_scraper)
}

def seed_all(session):
    for brand_name, (Extractor_Class, Scraper_Class) in BRAND_EXTRACTORS.items():
        extractor = Extractor_Class()
        scraper = Scraper_Class()
        data = extractor.load_csv(scraper.run())
        existing_names = [name for (name,) in session.query(Mouse.product_name).filter_by(brand_name=brand_name).all()]

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
            session.add(mouse)

            session.flush()

            if feature['tracking_speed'] is not None:
                gaming = Gaming_Mouse(
                    mouse_id = mouse.id,
                    acceleration = feature['max_acceleration'],
                    tracking_speed = feature['tracking_speed']
                )
                session.add(gaming)
    session.commit()

if __name__ == "__main__":
    session = create_session()
    seed_all(session)