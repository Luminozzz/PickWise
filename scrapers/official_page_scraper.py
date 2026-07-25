from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
from scrapers import config
from playwright_stealth import Stealth
from scrapers import human_behaviour
from word2num import word2num

class mouse_name_img_scraper:
    acer_official_url = "https://store.acer.com/en-sg/accessories/mouse?product_list_limit=all"
    ugreen_official_url = "https://www.ugreen.com/en-sg/collections/sg-mice"
    asus_official_url = "https://www.asus.com/sg/accessories/mice-and-mouse-pads/all-series/filter?Category=Wired-Mice,Wireless-Mice"

    def _get_img_src(self, img_tag):
        if img_tag is None:
            return None
        for attr in ('src', 'data-src', 'data-lazy-src'):
            val = img_tag.get(attr)
            if val and not val.startswith('data:'):
                return val
        return None

    def _data_check(self, product_name: str):
        return any(word.lower() in config.KEYWORDS_TO_EXCLUDE for word in product_name.split())

    def _clean_number(self, raw):
        raw = str(raw).strip().lower().replace(",", "").replace(" ", "")
        if raw.endswith("k"):
            return int(float(raw[:-1]) * 1000)
        try:
            return int(raw)
        except ValueError:
            try:
                return word2num(raw)
            except Exception:
                return raw

    def extract_polling_rates(self, text):
        rates = [self._clean_number(m) for m in config.PATTERNS["polling_rate"].findall(text)]
        rates = [r for r in rates if isinstance(r, int)]
        return max(rates) if rates else None

    def _data_clean_p1(self, mouse_name, brand_name, img_link, extra_info):
        specs = config.OUTPUT_DICT.copy()

        specs["product_name"] = mouse_name
        specs["brand_name"] = brand_name
        specs["img_link"] = img_link
        specs["other_features"] = extra_info

        if extra_info is None:
            return specs

        text = extra_info.lower()

        # Connectivity
        specs["wired"] = bool(re.search(config.PATTERNS["wired"], text))
        specs["bluetooth"] = bool(re.search(config.PATTERNS["bluetooth"], text))
        specs["dongle"] = any(re.search(p, text) for p in config.PATTERNS["dongle"])

        # left_fit and ergonomy
        specs["left_fit"] = "left" in text
        for shape, pattern in config.SHAPE_TERMS.items():
            if re.search(pattern, text, re.I):
                specs["ergonomy"] = shape
                break

        # RGB
        specs["rgb"] = bool(re.search(config.PATTERNS["rgb"], text, re.I))

        # max_DPI
        m = config.PATTERNS["max_DPI"].search(text)
        if m:
            specs["max_DPI"] = self._clean_number(m.group(1))

        # weight (grams)
        m = config.PATTERNS["weight"].search(text)
        if m:
            specs["weight"] = float(m.group(1))

        # number_of_buttons (from programmable_buttons pattern)
        m = config.PATTERNS["programmable_buttons"].search(text)
        if m:
            specs["number_of_buttons"] = self._clean_number(m.group(1))

        # battery_life
        batt = config.PATTERNS["battery_life"]
        match_month = batt["month"].search(text)
        if match_month:
            months = int(match_month.group(1)) * 30 * 24
            specs["battery_life"] = (months, months)
        else:
            match_day = batt["day"].search(text)
            if match_day:
                days = int(match_day.group(1)) * 24
                specs["battery_life"] = (days, days)
            else:
                match_hours = batt["hour"].findall(text)
                if match_hours:
                    hours = [int(h) for h in match_hours]
                    specs["battery_life"] = (min(hours), max(hours))

        # max_polling_rate
        specs["max_polling_rate"] = self.extract_polling_rates(text)

        # acceleration (IPS)
        m = config.PATTERNS["acceleration"].search(text)
        if m:
            specs["acceleration"] = int(m.group(1))

        # tracking_speed (G)
        m = config.PATTERNS["tracking_speed"].search(text)
        if m:
            specs["tracking_speed"] = int(m.group(1))

        return specs

    def scrape_acer_official_url(self):
        data_list = []

        with Stealth().use_sync(sync_playwright()) as p:
            browser = p.chromium.launch_persistent_context(**config.BROWSER_LAUNCH, **config.BROWSER_CONTEXT)
            browser.route(
                "**/*",
                lambda route: route.abort()
                if re.search(r"\.(png|jpe?g|gif|webp|svg|avif|woff2?|ttf|mp4)(\?|$)",
                            route.request.url, re.IGNORECASE)
                else route.continue_(),
            )
            page = browser.new_page()
            page.goto(self.acer_official_url)
            page.wait_for_timeout(timeout=10000)
            page.wait_for_load_state('networkidle', timeout = 100000)
            page.wait_for_timeout(timeout=30000)
            human_behaviour.scroll_to_bottom(page)

            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')
            product_pages = soup.select('li.item.product.product-item')

            print(product_pages)
            for product in product_pages:
                mouse_name = product.find('a', class_ = ['product-item-link'])
                img_link = product.find('img')
                div_extra_info = product.find('div', class_='product-item-description')
                if mouse_name is None:
                    continue
                mouse_name = mouse_name.get_text(strip=True)
                if self._data_check(mouse_name):
                    continue

                temp = {
                    "mouse_name": mouse_name,
                    "brand_name": "Acer",
                    "img_link": self._get_img_src(img_link),
                    "extra_info": "OFFICIAL PAGE \n" + " \n ".join([li.get_text(strip=True) for li in div_extra_info.find_all("li")]) if div_extra_info else None,
                }
                data_list.append(temp)
            browser.close()
        return data_list

    def scrape_ugreen_official_url(self):
        data_list = []

        with Stealth().use_sync(sync_playwright()) as p:
            browser = p.chromium.launch_persistent_context(**config.BROWSER_LAUNCH, **config.BROWSER_CONTEXT)
            browser.route(
                "**/*",
                lambda route: route.abort()
                if re.search(r"\.(png|jpe?g|gif|webp|svg|avif|woff2?|ttf|mp4)(\?|$)",
                            route.request.url, re.IGNORECASE)
                else route.continue_(),
            )
            page = browser.new_page()
            page.goto(self.ugreen_official_url)
            page.wait_for_selector("div.ug-main-collection", timeout=30000)
            page.wait_for_timeout(timeout=10000)
            html = page.content()

            soup = BeautifulSoup(html, "html.parser")
            products = soup.select('div.ug-product-card')
            print(products)
            for product in products:
                mouse_name = product.find('h3')
                img_link = product.find('img')
                print(mouse_name)
                print(img_link)
                if mouse_name is None or img_link is None:
                    continue
                mouse_name = mouse_name.get_text(strip=True)
                if self._data_check(mouse_name):
                    continue
                temp = {
                    "mouse_name": mouse_name,
                    "brand_name": "UGreen",
                    "img_link": self._get_img_src(img_link),
                    "extra_info": None
                }
                data_list.append(temp)
            browser.close()
        print(data_list)
        return data_list

    def scrape_asus_official_url(self):
        data_list = []

        with Stealth().use_sync(sync_playwright()) as p:
            browser = p.chromium.launch_persistent_context(**config.BROWSER_LAUNCH, **config.BROWSER_CONTEXT)
            browser.route(
                "**/*",
                lambda route: route.abort()
                if re.search(r"\.(png|jpe?g|gif|webp|svg|avif|woff2?|ttf|mp4)(\?|$)",
                            route.request.url, re.IGNORECASE)
                else route.continue_(),
            )
            page = browser.new_page()
            page.goto(self.asus_official_url)
            page.wait_for_selector('div#productListContainer')
            human_behaviour.scroll_to_bottom(page)
            page.wait_for_timeout(timeout=30000)

            html = page.content()

            soup = BeautifulSoup(html, 'html.parser')
            product_cards = soup.select('div#productListContainer div#productCardContainer')

            for product_card in product_cards:
                mouse_name = product_card.find('h2')
                img_link = product_card.find('img')
                extra_info = product_card.find('div', class_='itemModelSpec')

                if mouse_name is None or img_link is None:
                    continue
                mouse_name = mouse_name.get_text(strip=True)
                if self._data_check(mouse_name):
                    continue

                temp = {
                    "mouse_name": mouse_name,
                    "brand_name": "Asus",
                    "img_link": self._get_img_src(img_link),
                    "extra_info": "OFFICIAL PAGE \n" + extra_info.get_text(strip=True) if extra_info else None,
                }
                data_list.append(temp)
            browser.close()
        print(data_list)
        return data_list

    def run(self):
        raw = []
        raw.extend(self.scrape_acer_official_url())
        raw.extend(self.scrape_ugreen_official_url())
        raw.extend(self.scrape_asus_official_url())
        return [
            self._data_clean_p1(d["mouse_name"], d["brand_name"], d["img_link"], d["extra_info"])
            for d in raw
        ]

if __name__ == '__main__':
    spider = mouse_name_img_scraper()
    spider.run()