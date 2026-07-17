from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import urljoin
from scrapers import config
from playwright_stealth import Stealth
from scrapers import human_behaviour
from scrapers.image_utils import ugreen_hi_res
from scrapers.ecommerce_scraper import ecommerce_scraper
from word2num import word2num

class ugreen_scraper:
    ugreen_official_url = "https://www.ugreen.com/en-sg/collections/sg-mice"

    def is_blocked(self, page):
        try:
            title = page.title().lower()
            # Rendered visible text, not raw HTML source - the source can
            # contain a block marker incidentally (e.g. a reCAPTCHA <script>
            # tag's URL literally contains "captcha" on every normal page
            # load), which would otherwise read as a false block.
            body_start = page.inner_text("body")[:2000].lower()
        except Exception:
            return False
        return any(m in title or m in body_start for m in config.BLOCK_PAGE_MARKERS)

    def _goto_with_block_check(self, page, url, **kwargs):
        for attempt in range(1, config.MAX_ATTEMPTS_PER_PRODUCT + 1):
            page.goto(url, **kwargs)
            if not self.is_blocked(page):
                return True
            print(f"[ugreen_scraper] blocked at {url} (attempt {attempt}/{config.MAX_ATTEMPTS_PER_PRODUCT})")
            if attempt < config.MAX_ATTEMPTS_PER_PRODUCT:
                print(f"[ugreen_scraper] sleeping {config.BLOCK_BACKOFF_SECONDS}s before retry")
                time.sleep(config.BLOCK_BACKOFF_SECONDS)
        print(f"[ugreen_scraper] WARNING: giving up on {url} - still blocked after {config.MAX_ATTEMPTS_PER_PRODUCT} attempts")
        return False

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

    def _data_clean_p1(self, mouse_name, brand_name, img_link, extra_info, alt_image=None):
        specs = config.OUTPUT_DICT.copy()

        specs["product_name"] = mouse_name
        specs["brand_name"] = brand_name
        specs["img_link"] = img_link
        specs["alt_image"] = alt_image
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

    def _scrape_product_gallery(self, page, product_url):
        """Visit a single UGreen product page and return every image in its
        media gallery (product-gallery__main-wrapper), full-res, in display
        order. All gallery images are present in the initial HTML - no
        thumbnail clicking required."""
        if not self._goto_with_block_check(page, product_url):
            return []
        try:
            page.wait_for_selector('div.product-gallery__main-wrapper', timeout=15000)
        except Exception:
            return []
        page.wait_for_timeout(timeout=3000)

        soup = BeautifulSoup(page.content(), 'html.parser')
        wrapper = soup.select_one('div.product-gallery__main-wrapper')
        if wrapper is None:
            return []

        images = []
        seen = set()
        for media in wrapper.select('div.product__media-item[data-media-type="image"]'):
            src = ugreen_hi_res(self._get_img_src(media.find('img')))
            if src and src not in seen:
                seen.add(src)
                images.append(src)
        return images

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
            if not self._goto_with_block_check(page, self.ugreen_official_url):
                browser.close()
                return data_list
            page.wait_for_selector("div.ug-main-collection", timeout=30000)
            page.wait_for_timeout(timeout=10000)
            html = page.content()

            soup = BeautifulSoup(html, "html.parser")
            products = soup.select('div.ug-product-card')
            product_links = []
            for product in products:
                mouse_name = product.find('h3')
                link_tag = product.find('a', href=True)
                if mouse_name is None or link_tag is None:
                    continue
                mouse_name = mouse_name.get_text(strip=True)
                if self._data_check(mouse_name):
                    continue
                product_links.append((mouse_name, urljoin(self.ugreen_official_url, link_tag['href'])))

            for mouse_name, product_url in product_links:
                images = self._scrape_product_gallery(page, product_url)
                if not images:
                    print(f"[ugreen_scraper] WARNING: no gallery images for {mouse_name}")
                else:
                    temp = {
                        "mouse_name": mouse_name,
                        "brand_name": "UGreen",
                        "link": product_url,
                        "img_link": images[0],
                        "alt_image": "\n".join(images[1:]) if len(images) > 1 else None,
                        "extra_info": None
                    }
                    data_list.append(temp)
                human_behaviour.polite_delay()
            browser.close()
        if not data_list:
            print("[ugreen_scraper] WARNING: 0 products scraped from UGreen")
        return data_list

    # Translates an OUTPUT_DICT-shaped spec (this file's own working format,
    # shared with ecommerce_scraper) into the dict shape seed.py's
    # seed_all()/_seed_brand_data() expect (the same shape logitech_scraper
    # and asus_scraper's run() already return) - field names differ
    # (max_polling_rate -> polling_rate, acceleration -> max_acceleration),
    # a few DB-required fields (link, height) don't exist on OUTPUT_DICT at
    # all, and every column that's NOT NULL in the DB needs a concrete
    # default instead of None. UGreen has no colour variants on its site, so
    # the full image gallery (main + alt) becomes the single "Default"
    # colour's Mouse_Skins image list.
    def _to_seed_format(self, spec):
        alt_images = spec["alt_image"].split("\n") if spec.get("alt_image") else []
        gallery = ([spec["img_link"]] if spec.get("img_link") else []) + alt_images
        max_polling_rate = spec.get("max_polling_rate")

        return {
            "brand_name": spec["brand_name"],
            "link": spec.get("link"),
            "img_link": spec.get("img_link"),
            "colours": [{"Default": gallery}] if gallery else [],
            "ergonomy": spec.get("ergonomy") or "none",
            "left_fit": bool(spec.get("left_fit")),
            "battery_life": spec.get("battery_life") or (0, 0),
            "max_DPI": spec.get("max_DPI") or 0,
            "rgb": bool(spec.get("rgb")),
            "tracking_speed": spec.get("tracking_speed"),
            "max_acceleration": spec.get("acceleration"),
            "polling_rate": (125, max_polling_rate) if max_polling_rate else (125, 125),
            "weight": spec.get("weight") or 0.0,
            "length": spec.get("length") or 0.0,
            "width": spec.get("width") or 0.0,
            "height": 0.0,
            "number_of_buttons": spec.get("number_of_buttons") or 0,
            "bluetooth": bool(spec.get("bluetooth")),
            "dongle": bool(spec.get("dongle")),
            "wired": bool(spec.get("wired")),
            "other_features": spec.get("other_features"),
        }

    def run(self):
        raw = self.scrape_ugreen_official_url()
        cleaned = []
        for d in raw:
            spec = self._data_clean_p1(d["mouse_name"], d["brand_name"], d["img_link"], d["extra_info"], d.get("alt_image"))
            spec["link"] = d["link"]
            cleaned.append(spec)

        amazon = ecommerce_scraper()
        with Stealth().use_sync(sync_playwright()) as p:
            browser = p.chromium.launch_persistent_context(**config.BROWSER_LAUNCH, **config.BROWSER_CONTEXT)
            enriched = []
            for spec in cleaned:
                result = amazon.scrape_amazon_product(spec, browser)
                enriched.append(result if result is not None else spec)
                human_behaviour.polite_delay()
            browser.close()

        return {
            spec["product_name"]: self._to_seed_format(spec)
            for spec in enriched
        }

if __name__ == '__main__':
    spider = ugreen_scraper()
    spider.run()
