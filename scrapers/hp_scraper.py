import scrapy
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import urljoin
from scrapers import config
from scrapers.image_utils import hp_dedupe_gallery
from playwright_stealth import Stealth


class hp_scraper(scrapy.Spider):
    name = "hp_mouse_spider"
    listing_url = "https://www.hp.com/sg-en/shop/accessories/mice.html"

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
            print(f"[hp_scraper] blocked at {url} (attempt {attempt}/{config.MAX_ATTEMPTS_PER_PRODUCT})")
            if attempt < config.MAX_ATTEMPTS_PER_PRODUCT:
                print(f"[hp_scraper] sleeping {config.BLOCK_BACKOFF_SECONDS}s before retry")
                time.sleep(config.BLOCK_BACKOFF_SECONDS)
        print(f"[hp_scraper] WARNING: giving up on {url} - still blocked after {config.MAX_ATTEMPTS_PER_PRODUCT} attempts")
        return False

    # HP's Magento storefront shows a OneTrust consent banner on first visit.
    # Declining (rather than accepting) avoids adding marketing cookies to the
    # shared profile other scrapers reuse.
    def _dismiss_cookie_banner(self, page):
        for selector in (
            '#onetrust-reject-all-handler',
            '#onetrust-accept-btn-handler',
            'button[aria-label="Decline"]',
            'button[aria-label="Accept All"]',
        ):
            try:
                page.locator(selector).click(timeout=3000)
                return
            except Exception:
                continue

    @staticmethod
    def _sku_from_url(url):
        match = re.search(r'-([a-z0-9]+)\.html', url, re.IGNORECASE)
        return match.group(1).upper() if match else None

    # The listing header claims a total count but only renders ~15 cards per
    # page, so pages are walked via ?p= until a page adds no new URLs.
    def _collect_listing_urls(self, page):
        urls = set()
        page_num = 1
        while True:
            target = self.listing_url if page_num == 1 else f"{self.listing_url}?p={page_num}"
            if not self._goto_with_block_check(page, target, wait_until='domcontentloaded', timeout=config.PAGE_NAV_TIMEOUT):
                break
            if page_num == 1:
                self._dismiss_cookie_banner(page)
            try:
                page.wait_for_selector('li.product-item', timeout=config.DOM_WAIT_TIMEOUT)
            except PlaywrightTimeoutError:
                break

            soup = BeautifulSoup(page.content(), 'html.parser')
            cards = soup.select('li.product-item')
            if not cards:
                break

            before = len(urls)
            for card in cards:
                anchor = card.select_one('.product-item-photo-box a') or card.select_one('a[href]')
                if anchor and anchor.get('href'):
                    urls.add(urljoin(target, anchor['href']))
            if len(urls) == before:
                break
            page_num += 1
        return urls

    # The Fotorama gallery is JS-hydrated, but the full image list is embedded
    # as JSON in the page HTML - reading it directly works even without JS,
    # and is more reliable than waiting on the widget to render.
    @staticmethod
    def _extract_gallery(html):
        fulls = [m.replace('\\/', '/') for m in re.findall(r'"full"\s*:\s*"([^"]+)"', html)]
        seen = set()
        gallery = []
        for url in fulls:
            deduped = hp_dedupe_gallery(url)
            if deduped not in seen:
                seen.add(deduped)
                gallery.append(deduped)
        return gallery

    @staticmethod
    def _extract_specs(page):
        return page.evaluate("""() => {
            const out = {};
            document.querySelectorAll('#specs .product-spec-swapper').forEach(swap => {
                const group = swap.querySelector('.product-spec-group')?.textContent.trim();
                const attrs = {};
                swap.querySelectorAll('dl.product-spec-attribute').forEach(dl => {
                    const label = dl.querySelector('.label')?.textContent.trim();
                    const value = dl.querySelector('.value')?.textContent.trim();
                    if (label) attrs[label] = value || '';
                });
                if (group) out[group] = attrs;
            });
            return out;
        }""")

    # Swatches are CSS background colours, not <img> elements - each anchor's
    # own image is resolved later by visiting its variantUrl (see _load_detail).
    @staticmethod
    def _extract_colours(soup, page_url):
        colours = []
        container = soup.select_one('.product-view-choose-color')
        if container is None:
            return colours
        for anchor in container.select('a'):
            title = (anchor.get('title') or '').strip()
            text = anchor.get_text(strip=True)
            name_part, _, hex_part = (title or text).partition('|')
            style = anchor.get('style') or ''
            style_hex = re.search(r'background-color:\s*(#[0-9a-fA-F]{3,6})', style)
            href = anchor.get('href')
            if not name_part.strip() or not href:
                continue
            colours.append({
                'colour': name_part.strip(),
                'hex': hex_part.strip() or (style_hex.group(1) if style_hex else None),
                'variantUrl': urljoin(page_url, href),
            })
        return colours

    def _load_detail(self, page, url, cache):
        if url in cache:
            return cache[url]

        if not self._goto_with_block_check(page, url, wait_until='domcontentloaded', timeout=config.PAGE_NAV_TIMEOUT):
            cache[url] = None
            return None

        try:
            page.wait_for_selector('h1.page-title', timeout=config.SPEC_WAIT_TIMEOUT)
        except PlaywrightTimeoutError:
            pass
        try:
            page.wait_for_selector('#specs', timeout=config.SPEC_WAIT_TIMEOUT)
        except PlaywrightTimeoutError:
            pass

        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')

        name_el = soup.select_one('h1.page-title')
        name = name_el.get_text(strip=True) if name_el else (
            soup.title.get_text(strip=True) if soup.title else None
        )

        gallery = self._extract_gallery(html)
        specs = self._extract_specs(page)
        colours = self._extract_colours(soup, url)

        record = {
            'url': url,
            'name': name,
            'sku': self._sku_from_url(url),
            'primaryImage': gallery[0] if gallery else None,
            'gallery': gallery,
            'colours': colours,
            'specs': specs,
        }
        cache[url] = record
        return record

    def scrape_hp_mouse_details(self):
        products = []
        cache = {}

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

            urls = self._collect_listing_urls(page)
            print(f"[hp_scraper] {len(urls)} product URL(s) found on listing page(s)")

            for url in urls:
                record = self._load_detail(page, url, cache)
                if record is None:
                    continue

                if record['colours']:
                    for colour in record['colours']:
                        variant = self._load_detail(page, colour['variantUrl'], cache)
                        colour['variantSku'] = self._sku_from_url(colour['variantUrl'])
                        colour['imageLink'] = variant['primaryImage'] if variant else None
                else:
                    # Single-colour product - no swatch block on the page.
                    name_parts = record['name'].split(',', 1) if record['name'] else []
                    product_colour = (
                        (record['specs'].get('Appearance') or {}).get('Product Color')
                        or (name_parts[1].strip() if len(name_parts) > 1 else None)
                        or 'Default'
                    )
                    record['colours'] = [{
                        'colour': product_colour,
                        'hex': None,
                        'variantUrl': record['url'],
                        'variantSku': record['sku'],
                        'imageLink': record['primaryImage'],
                    }]

                products.append(record)

            browser.close()

        if not products:
            print("[hp_scraper] WARNING: 0 products scraped from HP")
        return products

    def hp_data_cleaning(self, products):
        format = {
            'link': None,
            'img_link': None,
            'colours': [],
            'ergonomy': "none",
            'left_fit': False,
            'battery_life': (0, 0),
            'max_DPI': 0,
            'rgb': False,
            # Unlike Razer's spec table, HP's never lists these - left as
            # None (not 0, and not a fake tuple for polling_rate) so
            # seed.py's `tracking_speed is not None or max_acceleration is
            # not None` check correctly skips creating a Gaming_Mouse row
            # for HP products, and no product is credited with a polling
            # rate HP never actually reported.
            'tracking_speed': None,
            'max_acceleration': None,
            'polling_rate': None,
            'weight': 0.0,
            'length': 0.0,
            'width': 0.0,
            'height': 0.0,
            'number_of_buttons': 0,
            'bluetooth': False,
            'dongle': False,
            'wired': False,
            'other_features': None,
        }
        data = {}
        for product in products:
            name = product.get('name')
            if not name:
                continue

            attrs = format.copy()
            attrs['brand_name'] = name.split(None, 1)[0]
            attrs['link'] = product['url']
            attrs['img_link'] = product['primaryImage']
            attrs['colours'] = [
                {c['colour']: c['imageLink']} for c in product['colours'] if c.get('imageLink')
            ]

            for rows in product['specs'].values():
                for label, value in rows.items():
                    if not value:
                        continue
                    result = self.extract_feature(label, value)
                    if result is None:
                        continue
                    items = result if isinstance(result, list) else [result]
                    for key, val in items:
                        if val is None:
                            continue
                        existing = attrs[key]
                        if key == 'other_features':
                            attrs[key] = (existing + val) if existing is not None else val
                        elif isinstance(val, str):
                            if val != "none":
                                attrs[key] = val
                        elif existing is not None and type(val) == type(existing) and val > existing:
                            attrs[key] = val

            # Connectivity rows are processed independently of each other
            # (e.g. HP's "Connectivity" and "Connection type" labels can each
            # carry partial info) - only fall back to wired once every row
            # for this product has been seen, or a still-ambiguous earlier
            # row would wrongly lock in "wired" before a later row's
            # bluetooth/dongle detail comes in.
            if not (attrs['bluetooth'] or attrs['dongle'] or attrs['wired']):
                attrs['wired'] = True

            attrs.update(config.HP_MANUAL_OVERRIDES.get(name, {}))

            data[name] = attrs
        return data

    def extract_feature(self, feature, value):
        feature = feature.lower()
        value = value.lower()

        if feature in config.HP_FORM_FACTOR:
            return [('left_fit', self.left_fit(value)),
                    ('ergonomy', self.ergonomy(value))]

        elif feature in config.HP_PROGRAMMABLE_BUTTONS:
            return ('number_of_buttons', self.number_of_buttons(value))

        elif feature in config.HP_CONNECTIVITY:
            return [('bluetooth', self.bluetooth(value)),
                    ('dongle', self.dongle(value)),
                    ('wired', self.wired(value))]

        elif feature in config.HP_BATTERY_LIFE:
            return ('battery_life', self.battery_life(value))

        elif feature in config.HP_MAX_DPI:
            return ('max_DPI', self.max_DPI(value))

        elif feature in config.HP_WEIGHT:
            return ('weight', self.weight(value))

        elif feature in config.HP_SIZE:
            return [('length', self.length(value)),
                    ('width', self.width(value)),
                    ('height', self.height(value))]

        else:
            return ('other_features', f"{feature}: {value}\n")

    def ergonomy(self, value: str) -> str:
        if "ergo" in value:
            return "ergonomic"
        elif "ambidextrous" in value:
            return "ambidextrous"
        return "none"

    def left_fit(self, value: str) -> bool:
        return "left" in value

    def number_of_buttons(self, value):
        match = re.search(r'(\d+)', value)
        return int(match.group(1)) if match else None

    def bluetooth(self, value):
        return "bluetooth" in value

    # "Dongle" never appears literally for the plain "2.4 GHz wireless
    # connection" phrasing HP uses on its "Connection type" rows - a 2.4GHz
    # radio link implies a USB receiver, so it's treated as one.
    def dongle(self, value):
        return "dongle" in value or "2.4" in value

    def wired(self, value):
        return "wired" in value

    def battery_life(self, value: str) -> tuple[int, int]:
        match_month = re.search(r'(\d+)\s*months?', value, re.IGNORECASE)
        if match_month:
            months = int(match_month.group(1)) * 30 * 24
            return (months, months)
        match_days = re.search(r'(\d+)\s*days?', value, re.IGNORECASE)
        if match_days:
            days = int(match_days.group(1)) * 24
            return (days, days)
        match_batt = re.findall(r'(\d+)\s*(?:hours?|hrs?|h)\b', value, re.IGNORECASE)
        if match_batt:
            hours = [int(match) for match in match_batt]
            return (min(hours), max(hours))
        return None

    def max_DPI(self, value: str) -> int:
        match = re.search(r'(\d+)', value)
        return int(match.group(1)) if match else None

    # HP mixes grams and kilograms across products (and even within one
    # HyperX product's "with cable" vs "mouse only" rows) - kg is always
    # written with a "kg" unit, so it's checked first to avoid the bare
    # "g" pattern matching the digits inside "kg" values.
    def weight(self, value: str) -> float:
        match = re.search(r'(\d+\.?\d*)\s*kg', value)
        if match:
            return float(match.group(1)) * 1000
        match = re.search(r'(\d+\.?\d*)\s*g\b', value)
        return float(match.group(1)) if match else None

    # Widest/narrowest plausible single-axis mouse dimension, in mm - guards
    # against HP occasionally dropping a decimal point on its own product
    # pages (e.g. one SKU lists "115 x 633 x 362 mm" where 633/362 should
    # read 63.3/36.2). Range comfortably covers every dimension actually
    # seen across HP's catalogue (~29-124mm per axis).
    _MIN_DIM_MM = 15.0
    _MAX_DIM_MM = 200.0

    # HP's own label is "(W x D x H)", not the L x W x H order Razer/Logitech
    # use - depth is the mouse's front-to-back axis, i.e. this project's
    # "length". Units also vary (mm vs cm) between products.
    def _dimensions_wdh(self, value: str):
        match = re.search(r'(\d+\.?\d*)\s*x\s*(\d+\.?\d*)\s*x\s*(\d+\.?\d*)\s*(mm|cm)', value)
        if not match:
            return None
        w, d, h, unit = match.groups()
        scale = 10.0 if unit == 'cm' else 1.0
        dims = (float(w) * scale, float(d) * scale, float(h) * scale)
        # Clamp each axis independently rather than reject the whole triplet -
        # usually only one figure in a corrupted row is actually wrong.
        return tuple(v if self._MIN_DIM_MM <= v <= self._MAX_DIM_MM else None for v in dims)

    def width(self, value: str) -> float:
        parsed = self._dimensions_wdh(value)
        return parsed[0] if parsed else None

    def length(self, value: str) -> float:
        parsed = self._dimensions_wdh(value)
        return parsed[1] if parsed else None

    def height(self, value: str) -> float:
        parsed = self._dimensions_wdh(value)
        return parsed[2] if parsed else None

    def run(self):
        products = self.scrape_hp_mouse_details()
        return self.hp_data_cleaning(products)


if __name__ == '__main__':
    spider = hp_scraper()
    spider.run()
