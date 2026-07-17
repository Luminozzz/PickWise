import urllib.request
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import time
from scrapers import config
from playwright_stealth import Stealth
from scrapers import human_behaviour

class asus_scraper:
    asus_official_url = "https://www.asus.com/sg/accessories/mice-and-mouse-pads/all-series/filter?Category=Wired-Mice,Wireless-Mice"

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
            print(f"[asus_scraper] blocked at {url} (attempt {attempt}/{config.MAX_ATTEMPTS_PER_PRODUCT})")
            if attempt < config.MAX_ATTEMPTS_PER_PRODUCT:
                print(f"[asus_scraper] sleeping {config.BLOCK_BACKOFF_SECONDS}s before retry")
                time.sleep(config.BLOCK_BACKOFF_SECONDS)
        print(f"[asus_scraper] WARNING: giving up on {url} - still blocked after {config.MAX_ATTEMPTS_PER_PRODUCT} attempts")
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

    # Finding every mouse card on the filtered listing page, along with its
    # own product page link (needed to pull the full spec table and colour
    # gallery, neither of which live on the listing card itself).
    def scrape_asus_official_url(self):
        data = {}

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
            if not self._goto_with_block_check(page, self.asus_official_url):
                browser.close()
                return data
            page.wait_for_selector('div#productListContainer')
            human_behaviour.scroll_to_bottom(page)
            page.wait_for_timeout(timeout=30000)

            html = page.content()

            soup = BeautifulSoup(html, 'html.parser')
            product_cards = soup.select('div#productListContainer div#productCardContainer')

            for product_card in product_cards:
                mouse_name = product_card.find('h2')
                img_link = product_card.find('img')
                link = product_card.find('a', href=True)

                if mouse_name is None or img_link is None or link is None:
                    continue
                mouse_name = mouse_name.get_text(strip=True)
                if self._data_check(mouse_name):
                    continue

                data[mouse_name] = {
                    'url': link['href'].split('?')[0],
                    'img_link': self._get_img_src(img_link),
                }
            browser.close()
        if not data:
            print("[asus_scraper] WARNING: 0 products scraped from Asus")
        return data

    # ROG's own template exposes the spec table under /spec/; the plain
    # www.asus.com template (used for ASUS-branded, non-ROG mice) uses
    # /techspec/ instead - same content, different route per site template.
    def _spec_url(self, url):
        base = url.rstrip('/')
        if 'rog.asus.com' in base:
            return base + '/spec/'
        return base + '/techspec/'

    def _extract_spec_rows(self, page):
        soup = BeautifulSoup(page.content(), 'html.parser')
        rows = []

        for row in soup.select('div.ProductSpecSingle__productSpecItemRow__BKwUK'):
            title = row.select_one('h2')
            content = row.select_one('div.ProductSpecSingle__productSpecItemContent__oJI5w')
            if title is None or content is None:
                continue
            feature = title.get_text(' ', strip=True)
            value = content.get_text(' | ', strip=True)
            if feature and value:
                rows.append((feature, value))
        if rows:
            return rows

        for row in soup.select('div.TechSpec__rowTable__1LR9D'):
            title = row.select_one('div.TechSpec__rowTableTitle__3GLj4')
            items = row.select('div[class*="rowTableItemViewBox"]')
            if title is None or not items:
                continue
            feature = title.get_text(' ', strip=True)
            value = ' | '.join(t for t in (it.get_text(' ', strip=True) for it in items) if t)
            if feature and value:
                rows.append((feature, value))
        return rows

    # Colour-name heuristic for the descriptive alt text ASUS writes for each
    # colour-swatch render, e.g. "An Iridescent White ASUS Fragrance Mouse
    # MD101 alongside ..." or "A hand holding ASUS SmartO Mouse Silent Plus
    # Green tea latte color placed on ...". There's no clean structured
    # colour label (unlike Razer/Logitech's swatch data-attributes) - when
    # the alt text names the colour right before the literal word "color",
    # walk backwards from there dropping any words that belong to the
    # product's own name until a genuine colour word is hit; otherwise fall
    # back to the word(s) between the leading article and "ASUS".
    def _colour_name(self, alt_text, product_name, index):
        if not alt_text:
            return f"Colour {index}"
        text = re.sub(r'\s+', ' ', alt_text).strip()
        # Strip the screen-reader "N of M " position prefix some swatch
        # slides carry (e.g. "1 of 2 A Rose Clay ASUS ...") - it would
        # otherwise break the leading-article anchor below.
        text = re.sub(r'^\d+\s+of\s+\d+\s+', '', text, flags=re.I)

        match = re.search(r'\bcolou?r\b', text, re.I)
        if match:
            before = text[:match.start()].strip()
            name_words = {w.lower() for w in re.findall(r'[A-Za-z]+', product_name or '')}
            stop_words = {'a', 'an', 'the', 'hand', 'holding', 'showcasing'}
            colour_words = []
            for word in reversed(before.split()):
                clean = re.sub(r'[^A-Za-z]', '', word).lower()
                if clean in name_words or clean in stop_words:
                    break
                colour_words.insert(0, word)
            if colour_words:
                return ' '.join(colour_words)

        match = re.match(r'^(?:an?|the)\s+(.+?)\s+ASUS\b', text, re.I)
        if match:
            return match.group(1).strip()

        return f"Colour {index}"

    # Some ASUS-branded (non-ROG) product pages render a colour-swatch
    # carousel (div.colors) whose real photos aren't <img src> at all - each
    # swatch's render is a CSS background-image set by a per-page generated
    # stylesheet (.../features/css/features.css, one per product's CMS
    # content), keyed by class img__color-N. Fetching that stylesheet and
    # reading the background-image URLs directly is far more reliable than
    # trying to get the browser to reveal it, since the rule only becomes
    # visible once its (cross-origin, JS-unreadable) stylesheet is applied.
    def extract_colours(self, page, product_name):
        soup = BeautifulSoup(page.content(), 'html.parser')
        colours_container = soup.select_one('div.colors')
        if colours_container is None:
            return []

        css_href = None
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href') or ''
            if 'features/css' in href:
                css_href = urljoin(page.url, href)
                break
        if css_href is None:
            return []

        try:
            req = urllib.request.Request(css_href, headers={'User-Agent': 'Mozilla/5.0'})
            css_text = urllib.request.urlopen(req, timeout=20).read().decode('utf-8', 'ignore')
        except Exception:
            return []

        # Prefer the 2x (higher-resolution) plain jpg render; fall back to 1x.
        images_by_index = {}
        for m in re.finditer(r'\.img__color-(\d+)\{background-image:url\(([^)]+/large/2x/[^)]+\.jpg)\)\}', css_text):
            images_by_index.setdefault(m.group(1), urljoin(css_href, m.group(2)))
        if not images_by_index:
            for m in re.finditer(r'\.img__color-(\d+)\{background-image:url\(([^)]+/large/1x/[^)]+)\)\}', css_text):
                images_by_index.setdefault(m.group(1), urljoin(css_href, m.group(2)))
        if not images_by_index:
            return []

        # The carousel library clones slides for infinite scrolling - only
        # the real (non-cloned) items should be read, or every colour would
        # be counted 2-3x over.
        real_items = [
            el for el in colours_container.select('.color-item')
            if el.find_parent(class_='slick-cloned') is None
        ]

        colours = []
        seen_names = set()
        for i, item in enumerate(real_items, start=1):
            img = item.select_one('img')
            if img is None:
                continue
            idx_match = next(
                (re.search(r'img__color-(\d+)', c) for c in (img.get('class') or []) if 'img__color' in c),
                None,
            )
            image_url = images_by_index.get(idx_match.group(1)) if idx_match else None
            if not image_url:
                continue
            alt = item.get('aria-label') or img.get('alt')
            colour_name = self._colour_name(alt, product_name, i)
            if colour_name in seen_names:
                continue
            seen_names.add(colour_name)
            colours.append({colour_name: [image_url]})
        return colours

    def scraper_asus_mouse_details(self, mouse_links: dict):
        data = []
        failed = []

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

            for name, val in mouse_links.items():
                url = val['url']
                ok = False

                for attempt in (1, 2):  # one retry for transient nav failures
                    try:
                        print(f"-> {name} (attempt {attempt}): {url}")
                        if not self._goto_with_block_check(page, url, wait_until='domcontentloaded', timeout=config.PAGE_NAV_TIMEOUT):
                            raise RuntimeError("blocked (overview)")
                        page.wait_for_timeout(4000)

                        colours = self.extract_colours(page, name)

                        data.append({'product_name': name, 'feature': 'link', 'value': url})
                        data.append({'product_name': name, 'feature': 'img_link', 'value': val['img_link']})
                        data.append({'product_name': name, 'feature': 'colours', 'value': colours})

                        spec_url = self._spec_url(url)
                        if not self._goto_with_block_check(page, spec_url, wait_until='domcontentloaded', timeout=config.PAGE_NAV_TIMEOUT):
                            raise RuntimeError("blocked (spec)")
                        # state="attached" rather than the default "visible" -
                        # TechSpec's rows are attached to the DOM well before
                        # they're scrolled into view/animated in, and we only
                        # need the HTML content, not actual visibility.
                        page.wait_for_selector(
                            'div.ProductSpecSingle__productSpecItemRow__BKwUK, div.TechSpec__rowTable__1LR9D',
                            state='attached',
                            timeout=config.SPEC_WAIT_TIMEOUT,
                        )
                        page.wait_for_timeout(1500)

                        seen = set()
                        rows_added = 0
                        for feature, value in self._extract_spec_rows(page):
                            key = (feature, value)
                            if key in seen:
                                continue
                            seen.add(key)
                            data.append({'product_name': name, 'feature': feature, 'value': value})
                            rows_added += 1
                        print(f"   ok - {rows_added} spec rows, {len(colours)} colour(s)")

                        ok = True
                        break  # success - stop retrying

                    except Exception as e:
                        print(f"   attempt {attempt} failed: {type(e).__name__}: {e}")
                human_behaviour.polite_delay()
                if not ok:
                    failed.append(name)

            page.close()
            browser.close()

        if failed:
            print(f"\n{len(failed)} product(s) failed: {failed}")
        return data

    def asus_data_cleaning(self, extracted_data):
        format = {
            'link': None,
            'img_link': None,
            'colours': [],
            'ergonomy': "none",
            'left_fit': False,
            'battery_life': (0, 0),
            'max_DPI': 0,
            'rgb': False,
            'tracking_speed': None,
            'max_acceleration': None,
            'polling_rate': (1000, 1000),
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
        for detail in extracted_data:
            product_name = detail['product_name']
            feature = detail['feature']
            value = detail['value']

            if product_name not in data:
                data[product_name] = format.copy()
                data[product_name]['brand_name'] = 'Asus'

            if feature in ("link", "img_link", "colours"):
                data[product_name][feature] = value
                continue

            result = self.extract_feature(feature, value)
            if result is None:
                continue
            items = result if isinstance(result, list) else [result]
            for key, val in items:
                if val is None:
                    continue
                existing = data[product_name][key]
                if key == 'other_features':
                    data[product_name][key] = (existing + val) if existing is not None else val
                elif isinstance(val, bool):
                    data[product_name][key] = existing or val
                elif isinstance(val, tuple):
                    if val == format[key]:
                        pass
                    elif existing == format[key]:
                        data[product_name][key] = val
                    else:
                        data[product_name][key] = (min(existing[0], val[0]), max(existing[1], val[1]))
                elif isinstance(val, str):
                    if val != "none":
                        data[product_name][key] = val
                # tracking_speed/max_acceleration default to None (not 0) so
                # seed.py can tell "never reported" apart from a genuine
                # zero - existing being None must still accept the first
                # real value seen, not just a strictly-greater one.
                elif existing is None or (type(val) == type(existing) and val > existing):
                    data[product_name][key] = val
        return data

    def extract_feature(self, feature, value):
        feature = feature.lower()
        value = value.lower()

        if feature in config.ASUS_SKIP_FIELDS:
            return None

        if any(keyword in feature for keyword in config.ASUS_FORM_FACTOR):
            return [('left_fit', self.left_fit(value)),
                    ('ergonomy', self.ergonomy(value))]

        elif any(keyword in feature for keyword in config.ASUS_CONNECTIVITY):
            bluetooth = self.bluetooth(value)
            dongle = self.dongle(value)
            wired = self.wired(value)
            if not (bluetooth or dongle or wired):
                wired = True  # default to wired when nothing is detected
            return [('bluetooth', bluetooth),
                    ('dongle', dongle),
                    ('wired', wired)]

        elif any(keyword in feature for keyword in config.ASUS_PROGRAMMABLE_BUTTONS):
            return ('number_of_buttons', self.number_of_buttons(value))

        elif any(keyword in feature for keyword in config.ASUS_BATTERY_LIFE):
            return ('battery_life', self.battery_life(value))

        elif any(keyword in feature for keyword in config.ASUS_MAX_DPI):
            return ('max_DPI', self.max_DPI(value))

        elif any(keyword in feature for keyword in config.ASUS_TRACKING_SPEED):
            return ('tracking_speed', self.tracking_speed(value))

        elif any(keyword in feature for keyword in config.ASUS_MAX_ACCELERATION):
            return ('max_acceleration', self.max_acceleration(value))

        elif any(keyword in feature for keyword in config.ASUS_WEIGHT):
            return ('weight', self.weight(value))

        elif any(keyword in feature for keyword in config.ASUS_SIZE):
            length, width, height = self.dimensions(value)
            return [('length', length), ('width', width), ('height', height)]

        elif any(keyword in feature for keyword in config.ASUS_POLLING_RATE):
            return ('polling_rate', self.polling_rate(value))

        elif any(keyword in feature for keyword in config.ASUS_RGB):
            return ('rgb', self.rgb(value))

        else:
            return ('other_features', f"{feature}: {value}\n")

    def ergonomy(self, value: str) -> str:
        if "ambidextrous" in value:
            return "ambidextrous"
        elif "ergo" in value:
            return "ergonomic"
        elif "symmetrical" in value:
            return "symmetrical"
        return "none"

    def left_fit(self, value: str) -> bool:
        return "left" in value

    def number_of_buttons(self, value):
        match = re.search(r'(\d+)', value)
        return int(match.group(1)) if match else None

    def bluetooth(self, value):
        return "bluetooth" in value

    def dongle(self, value):
        return bool(re.search(r'2\.4\s*ghz', value)) or "wireless" in value

    def wired(self, value):
        return bool(re.search(r'\busb\b', value)) or "wired" in value

    def battery_life(self, value: str) -> tuple[int, int]:
        match_month = re.search(r'(\d+)\s*months?', value, re.IGNORECASE)
        if match_month:
            months = int(match_month.group(1)) * 30 * 24
            return (months, months)
        match_days = re.search(r'(\d+)\s*days?', value, re.IGNORECASE)
        if match_days:
            days = int(match_days.group(1)) * 24
            return (days, days)
        match_batt = re.findall(r'(\d+)\s*\+?\s*(?:hours?|hrs?|h)\b', value, re.IGNORECASE)
        if match_batt:
            hours = [int(match) for match in match_batt]
            return (min(hours), max(hours))
        return None

    def max_DPI(self, value: str) -> int:
        nums = [int(n.replace(',', '')) for n in re.findall(r'([\d,]+)\s*dpi', value, re.I)]
        return max(nums) if nums else None

    def tracking_speed(self, value: str) -> int:
        match = re.search(r'(\d+)\s*ips\b', value, re.IGNORECASE)
        return int(match.group(1)) if match else None

    def max_acceleration(self, value: str) -> int:
        match = re.search(r'(\d+)\s*g\b', value, re.IGNORECASE)
        return int(match.group(1)) if match else None

    def weight(self, value: str) -> float:
        match = re.search(r'(\d+\.?\d*)\s*g\b', value)
        return float(match.group(1)) if match else None

    # ASUS lists dimensions as "L(...)xW(...)xH(...) mm" or "L x W x H mm"
    # (occasionally with "*" instead of "x") - always in that axis order, so
    # just pulling the first three numbers out in sequence works regardless
    # of which separator/unit-label style a given product page uses.
    def dimensions(self, value: str):
        nums = re.findall(r'(\d+\.?\d*)', value)
        if len(nums) >= 3:
            return float(nums[0]), float(nums[1]), float(nums[2])
        return None, None, None

    def polling_rate(self, value: str) -> tuple[int, int]:
        match = re.findall(r'(\d+)\s*hz', value, re.IGNORECASE)
        if not match:
            return None
        rates = [int(m) for m in match]
        return (1000, max(rates))

    def rgb(self, value):
        return "yes" in value

    def run(self):
        mouse_links = self.scrape_asus_official_url()
        data = self.scraper_asus_mouse_details(mouse_links)
        cleaned_data = self.asus_data_cleaning(data)
        for attrs in cleaned_data.values():
            if attrs.get('colours'):
                continue  # already populated with per-colour galleries
            attrs['colours'] = [{'Default': [attrs.get('img_link')]}]
        return cleaned_data

if __name__ == '__main__':
    spider = asus_scraper()
    spider.run()
