from playwright.sync_api import sync_playwright, BrowserContext
from bs4 import BeautifulSoup
import re, json
from scrapers import config
from playwright_stealth import Stealth
from scrapers import human_behaviour
from rapidfuzz import fuzz
import copy

class ecommerce_scraper:

    shopee_store_url = "https://shopee.sg/"
    amazon_store_url = "https://www.amazon.sg/"
    lazada_store_url = "https://www.lazada.sg/"

    def _normalise(self, s: str):
        return " ".join(s.lower().replace("-", " ").split())

    def _score_product_title(self, product_card_name, target_brand, target_product):
        if any(w in product_card_name for w in config.KEYWORDS_TO_EXCLUDE):
            return 0
        if target_brand.lower() not in product_card_name:
            return 0
        tokens = set(product_card_name.split())
        model_tokens = set(self._normalise(target_product).split())

        if not model_tokens.issubset(tokens):
            return 0
        return fuzz.token_set_ratio(product_card_name, self._normalise(f"{target_brand} {target_product}"))

    def _fill_remaining_from_text(self, output, text):
        """Backfill spec fields Amazon's known-key table (AMAZON_* constants)
        doesn't cover, by sweeping the same free-text patterns the official-page
        scrapers use. Only fills fields still unset - the structured key
        mapping above is more reliable than a blind regex sweep, so it always
        wins when both find something."""
        if not text:
            return output
        text = text.lower()

        if output.get('rgb') is None and re.search(config.PATTERNS["rgb"], text, re.I):
            output['rgb'] = True

        if not output.get('ergonomy'):
            for shape, pattern in config.SHAPE_TERMS.items():
                if re.search(pattern, text, re.I):
                    output['ergonomy'] = shape
                    break

        if output.get('max_polling_rate') is None:
            rates = [int(m.replace(',', '')) for m in config.PATTERNS["polling_rate"].findall(text)]
            if rates:
                output['max_polling_rate'] = max(rates)

        if output.get('acceleration') is None:
            m = config.PATTERNS["acceleration"].search(text)
            if m:
                output['acceleration'] = int(m.group(1))

        if output.get('tracking_speed') is None:
            m = config.PATTERNS["tracking_speed"].search(text)
            if m:
                output['tracking_speed'] = int(m.group(1))

        return output

    def scrape_amazon_product(self, input: dict, browser: BrowserContext):
        page = browser.new_page()
        output = copy.deepcopy(input)

        product_name = input['product_name']
        product_brand = input['brand_name']
        try:
            product_pool = []
            search_url = self.amazon_store_url + "s?k=" + "+".join(product_name.split(" "))
            page.goto(search_url)
            human_behaviour.human_pause(page, 800, 2000)
            human_behaviour.human_mouse_move(page)
            human_behaviour.human_scroll(page)
            page.wait_for_selector('div[role="listitem"]', state = "visible", timeout=60000)
            page.wait_for_timeout(timeout=7000)
            human_behaviour.human_pause(page, 1500, 4000)
            human_behaviour.human_mouse_move(page)

            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')

            divs = soup.find_all('div', attrs={'role': 'listitem'}, limit=config.NUMBER_OF_PRODUCTS_COMPARISON)
            for div in divs:
                title_elem = div.find('div', attrs = {'data-cy': 'title-recipe'}).find('a', recursive=False).find('span')
                brand_name_tag = div.select_one("h2.s-line-clamp-1 span.a-size-base-plus")
                price_elem = div.find('div', attrs={'data-cy': 'price-recipe'}).find('span', class_ = 'a-offscreen')
                review_elem = div.find('div', attrs={'data-cy': 'reviews-block'})
                if brand_name_tag:
                    brand_name = brand_name_tag.get_text(strip=True)
                else:
                    continue

                if review_elem is None:
                    num_of_stars = 0.0
                    num_of_reviews = 0
                else:
                    num_of_stars = review_elem.find('span', class_ = ['a-size-small', 'a-color-base']).text
                    num_of_reviews = review_elem.find('span', class_ = ['a-size-mini', 'puis-normal-weight-text']).text

                    num_of_reviews = str(num_of_reviews).strip("()").upper()
                    if 'K' in num_of_reviews:
                        num_of_reviews = int(float(num_of_reviews.replace('K','')) * 1000)
                    elif 'M' in num_of_reviews:
                        num_of_reviews = int(float(num_of_reviews.replace('M','')) * 1_000_000)
                    else:
                        num_of_reviews = int(num_of_reviews)
                title = title_elem.text.strip()
                #clean_title = re.search(r'(.+?)(?:\s*[-,]\s*)',title).group(1).strip() if re.search(r'(.+?)(?:\s*[-,]\s*)',title) else title.strip()

                if brand_name not in title:
                    title = brand_name + " " + title

                # num_of_ele = len(product_name.split()) + config.NUMBER_OF_EXTRA_WORDS
                # clean_title_v1 = " ".join((clean_title.split())[:num_of_ele])
                # clean_title_v2 = " ".join((title.split())[:num_of_ele])
                # score = max(fuzz.WRatio(product_name, clean_title_v1), fuzz.WRatio(product_name, clean_title_v2))

                score = self._score_product_title(title, product_brand, product_name)
                ASIN = div['data-asin']
                product_pool.append({
                    'title': title,
                    # 'clean_title_v1': clean_title_v1,
                    # 'clean_title_v2': clean_title_v2,
                    'ASIN': ASIN,
                    'num_of_stars': float(num_of_stars),
                    'num_of_reviews': num_of_reviews,
                    'score': score
                })

            max_score_candidate = max(product_pool, key = lambda x: x['score'])
            link = f'https://www.amazon.sg/dp/{max_score_candidate["ASIN"]}'

            human_behaviour.human_mouse_move(page)
            human_behaviour.human_pause(page, 2000, 5000)
            print(link)
            page.goto(link)
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')

            match = re.search(r"'colorImages':\s*\{\s*'initial':\s*(\[.*?\])\s*\}", html, re.DOTALL)

            hi_res_images = []
            if match:
                raw = match.group(1)

                hi_res_images = re.findall(r'"hiRes":"(https:[^"]+)"', raw)

                if not hi_res_images:
                    hi_res_images = re.findall(r"'hiRes':'(https:[^']+)'", raw)
            # An official-page scraper's own gallery (when present) is the
            # preferred source - only fall back to Amazon's images if this
            # product doesn't already carry one.
            if hi_res_images and not output.get('alt_image'):
                output['alt_image'] = "\n".join(hi_res_images)

            # product specifications
            product_info_dict = {}
            product_info_str = "\n AMAZON \n"
            for table in soup.select("table.prodDetTable"):
                for row in table.select("tr"):
                    th = row.find("th")
                    td = row.find("td")
                    if th and td:
                        key = th.get_text(strip=True)
                        value = td.get_text(strip=True)
                        if key:

                            if config.AMAZON_CONNECTIVITY_TECHNOLOGY in product_info_dict and key == config.AMAZON_POWER_SOURCE:
                                product_info_dict[config.AMAZON_CONNECTIVITY_TECHNOLOGY] = product_info_dict[config.AMAZON_CONNECTIVITY_TECHNOLOGY] + " " + value
                            else:
                                product_info_dict[key] = value
                            product_info_str = product_info_str + f"{key}: {value} \n"


            for key, value in product_info_dict.items():
                key = key.lower()
                value = value.lower()
                if key == config.AMAZON_CONNECTIVITY_TECHNOLOGY:
                    # connectivity
                    if "usb" in value:
                        if "battery" in value:
                            output['dongle'] = True
                        if "corded" in value:
                            output['wired'] = True
                    if "bluetooth" in value:
                        output['bluetooth'] = True

                if key == config.AMAZON_BUTTON_QUANTITY:

                    m = re.search(r'(\d+)', value)
                    if m:
                        output['number_of_buttons'] = int(m.group(1))

                if key == config.AMAZON_HAND_ORIENTATION:
                    if "left" in value:
                        output['left_fit'] = True
                    elif "ambidextrous" in value:
                        output['ergonomy'] = "ambidextrous"

                if key == config.AMAZON_BATTERY_AVERAGE_LIFE:
                    batt = config.PATTERNS["battery_life"]
                    match_month = batt["month"].search(value)
                    if match_month:
                        months = int(match_month.group(1)) * 30 * 24
                        output["battery_life"] = (months, months)
                    else:
                        match_day = batt["day"].search(value)
                        if match_day:
                            days = int(match_day.group(1)) * 24
                            output["battery_life"] = (days, days)
                        else:
                            match_hours = batt["hour"].findall(value)
                            if match_hours:
                                hours = [int(h) for h in match_hours]
                                output["battery_life"] = (min(hours), max(hours))

                if key == config.AMAZON_MOUSE_MAXIMUM_SENSITIVITY:

                    m = re.search(r'(\d+)', value)
                    if m:
                        output['max_DPI'] = int(m.group(1))

                if key == config.AMAZON_ITEM_WEIGHT:

                    m = re.search(r'(\d+)', value)
                    if m:
                        number = int(m.group(1))
                        if "gram" in value or re.search(r'\bg\b', value):
                            output['weight'] = number
                        elif "pound" in value or re.search(r'\blb\b', value):
                            output['weight'] = number * config.POUNDS_TO_GRAMS

                if key == config.AMAZON_ITEM_DIMENSIONS_L_X_W:

                    ele = re.search(r'(\d+(?:\.\d+)?)lx(\d+(?:\.\d+)?)w', value)
                    if ele:
                        length = float(ele.group(1))
                        width = float(ele.group(2))

                        if "centimetres" in value or "cm" in value:
                            output['length'] = length * config.CENTIMETRES_TO_MILLIMETRES
                            output['width'] = width * config.CENTIMETRES_TO_MILLIMETRES
                        elif "millimetres" in value or "mm" in value:
                            output['length'] = length
                            output['width'] = width

            output = self._fill_remaining_from_text(output, product_info_str)

            print(output)
            if output['other_features']:
                output['other_features'] = output['other_features'] + product_info_str
            else:
                output['other_features'] = product_info_str
            return output
        except Exception as e:
            print(f"failed: {type(e).__name__}: {e} \   n {product_name}")

    def scrape_shopeee_product(self, input: dict, browser: BrowserContext):
        page = browser.new_page()
        output = copy.deepcopy(input)

        product_name = input['product_name']
        product_brand = input['brand_name']
        try:
            product_pool = []
            search_url = self.amazon_store_url + "s?k=" + "+".join(product_name.split(" "))
            page.goto(search_url)
            human_behaviour.human_pause(page, 800, 2000)
            human_behaviour.human_mouse_move(page)
            human_behaviour.human_scroll(page)
            page.wait_for_selector('div[role="listitem"]', state = "visible", timeout=60000)
            page.wait_for_timeout(timeout=7000)
            human_behaviour.human_pause(page, 1500, 4000)
            human_behaviour.human_mouse_move(page)

            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')
            output['other_features'] = output['other_features'] + product_info_str
            return output
        except Exception as e:
            print(f"failed: {type(e).__name__}: {e} \n {product_name}")

if __name__ == '__main__':
    crawler = ecommerce_scraper()
    exam = config.OUTPUT_DICT.copy()
    exam['product_name'] = 'Razer Viper V4 Pro'
    exam['brand_name'] = 'Razer'

    with Stealth().use_sync(sync_playwright()) as p:
        browser = p.chromium.launch_persistent_context(**config.BROWSER_LAUNCH, **config.BROWSER_CONTEXT)
        browser.route(
            "**/*",
            lambda route: route.abort()
            if re.search(r"\.(png|jpe?g|gif|webp|svg|avif|woff2?|ttf|mp4)(\?|$)",
                        route.request.url, re.IGNORECASE)
            else route.continue_(),
        )
        print(crawler.scrape_amazon_product(exam, browser))
        browser.close()
