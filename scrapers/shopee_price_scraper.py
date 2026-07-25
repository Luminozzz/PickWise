import scrapy
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import random
import time
import datetime
from rapidfuzz import fuzz
from scrapers import config
from playwright_stealth import Stealth
from scrapers import human_behaviour

class shopee_new_product_price_scraper(scrapy.Spider):
    name = "shopee_new_product_price_scraper"
    shopee_store_url = "https://shopee.sg/"

    # robots.txt (User-agent: *) sets Crawl-delay: 1 - every request to
    # shopee.sg (a /search?keyword= or a product's own page) waits at least
    # this long since the previous one, on top of human_behaviour's own
    # randomised pauses (which already exceed 1s, but this is an explicit,
    # guaranteed floor rather than an incidental one). Clicking between
    # colour swatches on an already-loaded product page is a client-side
    # re-render, not a new page request, so it isn't rate-limited here.
    # Only /search?keyword= and a product's own detail page are ever
    # requested - both allowed for User-agent:*; every Disallow rule in
    # robots.txt (cart/checkout/user/order, *-i.*/similar,
    # find_similar_products/you_may_also_like/top_products,
    # /search*searchPrefill, mall/just-for-you/, etc) targets paths this
    # scraper never visits.
    CRAWL_DELAY_SECONDS = 1.0

    def __init__(self):
        super().__init__()
        self._last_request_at = 0.0

    def _respect_crawl_delay(self):
        elapsed = time.monotonic() - self._last_request_at
        remaining = self.CRAWL_DELAY_SECONDS - elapsed
        if remaining > 0:
            time.sleep(remaining)
        self._last_request_at = time.monotonic()

    def is_blocked(self, page):
        try:
            title = page.title().lower()
            # Rendered visible text, not raw HTML source - the source can
            # contain a block marker incidentally, which would otherwise
            # read as a false block.
            body_start = page.inner_text("body")[:2000].lower()
        except Exception:
            return False
        # Shopee's own gate ("Page Unavailable ... Looks like you're not
        # logged in yet") isn't a captcha/challenge page, so it isn't caught
        # by config.BLOCK_PAGE_MARKERS - checked separately here.
        shopee_markers = ("page unavailable", "not logged in yet")
        return (any(m in title or m in body_start for m in config.BLOCK_PAGE_MARKERS)
                or any(m in title or m in body_start for m in shopee_markers))

    @staticmethod
    def parse_sold(sold_text):
        """Convert '1k+ sold' / '529 sold' / '1.2k Ratings' -> int."""
        if not sold_text:
            return 0
        text = sold_text.lower().strip()
        m = re.search(r"([\d.,]+)\s*([km]?)", text)
        if not m:
            return 0
        number = float(m.group(1).replace(",", ""))
        multiplier = {"k": 1_000, "m": 1_000_000}.get(m.group(2), 1)
        return int(number * multiplier)

    @staticmethod
    def parse_price(price_text):
        """Convert '48.25' or '$1,299.00' -> float. Returns None if unparseable."""
        if not price_text:
            return None
        m = re.search(r"[\d,]+(?:\.\d+)?", price_text)
        if not m:
            return None
        return float(m.group(0).replace(",", ""))

    # Search once per mouse, using only its default skin's product name (no
    # colour appended) - other colours are matched later straight off the
    # winning product's own page, not by searching per-colour. Every skin
    # passed in (default or not) still feeds skins_by_product, so phase 2
    # knows every colour this mouse actually has in our DB even though only
    # the default entry triggers a search.
    def scrape_shopee_price(self, lst_of_mouse):
        data = []
        failed = []

        skins_by_product = {}
        for m in lst_of_mouse:
            skins_by_product.setdefault(m['product_name'], {})[m['colour']] = m['skin_id']

        with Stealth().use_sync(sync_playwright()) as p:
            browser = p.chromium.launch_persistent_context(**config.BROWSER_LAUNCH, **config.BROWSER_CONTEXT)
            browser.route("**/*",
                lambda route: route.abort()
                if re.search(r"\.(png|jpe?g|gif|webp|svg|avif|woff2?|ttf|mp4)(\?|$)",
                            route.request.url, re.IGNORECASE)
                else route.continue_()
                )
            page = browser.new_page()

            for mouse in human_behaviour.shuffled_subset(lst_of_mouse):
                # The first (lowest skin id) colour created for a mouse is
                # always its default - seed.py marks that one entry
                # is_default=True. Every other colour is only used below to
                # tell which of Shopee's own variants are ours to match.
                if not mouse.get('is_default'):
                    continue

                search_text = mouse['product_name'].strip()
                ok = False

                for attempt in range(1, config.MAX_ATTEMPTS_PER_PRODUCT + 1):
                    try:
                        if self.is_blocked(page):
                            print(f"{search_text}: looks blocked, sleeping {config.BLOCK_BACKOFF_SECONDS}s")
                            time.sleep(config.BLOCK_BACKOFF_SECONDS)
                            raise RuntimeError("blocked")

                        product_pool = []
                        self._respect_crawl_delay()
                        search_url = self.shopee_store_url + "search?keyword=" + "%20".join(search_text.split(" "))
                        page.goto(search_url)
                        human_behaviour.human_pause(page, 800, 2000)
                        human_behaviour.human_mouse_move(page)
                        human_behaviour.human_scroll(page)
                        page.evaluate(f"window.scrollBy(0, {random.randint(300, 1000)})")
                        page.wait_for_selector('li.shopee-search-item-result__item', state="visible", timeout=60000)
                        page.wait_for_timeout(timeout=7000)
                        human_behaviour.human_pause(page, 1500, 4000)
                        human_behaviour.human_mouse_move(page)

                        if self.is_blocked(page):
                            print(f"{search_text}: looks blocked, sleeping {config.BLOCK_BACKOFF_SECONDS}s")
                            time.sleep(config.BLOCK_BACKOFF_SECONDS)
                            raise RuntimeError("blocked")

                        html = page.content()
                        soup = BeautifulSoup(html, 'html.parser')

                        # Find the first n products out of the n
                        divs = soup.select("li.shopee-search-item-result__item", limit=config.NUMBER_OF_PRODUCTS_COMPARISON)
                        for div in divs:
                            # A sponsored/video/brand-shelf card can match this
                            # same selector while carrying a totally different
                            # internal structure - skip just this one card
                            # rather than aborting the whole search.
                            try:
                                title_elem = div.find("div", class_=re.compile(r"line-clamp-2"))
                                anchor = div.find('a', href=True)
                                price_node = div.find(string=re.compile(r"\$\s?[\d,]+(?:\.\d+)?"))
                                sold_elem = div.find(string=re.compile(r"\bsold\b", re.I))

                                if title_elem is None or anchor is None:
                                    print(search_text + ": title/link cannot be found")
                                    continue
                                if price_node is None:
                                    print(search_text + ": price cannot be found")
                                    continue

                                price = self.parse_price(str(price_node))
                                if price is None:
                                    continue

                                num_of_sold = self.parse_sold(str(sold_elem)) if sold_elem else 0

                                rating_elem = 0.0
                                for span in div.find_all("span"):
                                    txt = span.get_text(strip=True)
                                    if re.fullmatch(r"[0-5](?:\.\d)?", txt):
                                        rating_elem = float(txt)
                                        break

                                title = title_elem.text.strip()
                                link = urljoin(self.shopee_store_url, anchor['href'])
                                clean_title = re.search(r'(.+?)(?:\s*[-,]\s*)', title).group(1).strip() if re.search(r'(.+?)(?:\s*[-,]\s*)', title) else title.strip()

                                num_of_ele = len(search_text.split()) + config.NUMBER_OF_EXTRA_WORDS
                                clean_title_v1 = " ".join((clean_title.split())[:num_of_ele])
                                clean_title_v2 = " ".join((title.split())[:num_of_ele])
                                score = max(fuzz.WRatio(search_text, clean_title_v1), fuzz.WRatio(search_text, clean_title_v2))
                                product_pool.append({
                                    'title': title,
                                    'link': link,
                                    'price': price,
                                    'num_of_sold': num_of_sold,
                                    'num_of_ratings': rating_elem,
                                    'score': score
                                })
                            except Exception as e:
                                print(f"{search_text}: skipping unparsable result card ({type(e).__name__}: {e})")
                                continue

                        if not product_pool:
                            print(search_text + ": price not found")
                            ok = True
                            break

                        exact_words = search_text.lower().split()[1:]
                        filter_no_price_and_name_exists = [p for p in product_pool if all(word in re.findall(r'[a-z0-9]+', p['title'].lower()) for word in exact_words)]
                        if not filter_no_price_and_name_exists:
                            print(search_text + ": price not found")
                            ok = True
                            break

                        # max_score (and thus score_diff) is taken from this
                        # already word/price-filtered set, not the raw
                        # product_pool - see amazon_price_scraper.py for why.
                        max_score = max(p['score'] for p in filter_no_price_and_name_exists)
                        for product in filter_no_price_and_name_exists:
                            product['score_diff'] = max_score - product['score']

                        candidates_for_price = [p for p in filter_no_price_and_name_exists if p['score_diff'] <= config.SIMILARITY_SCORE_DIFFERENCE_THRESHOLD and all(word not in config.KEYWORDS_TO_EXCLUDE for word in re.findall(r'[a-z0-9]+', p['title'].lower()))]
                        if not candidates_for_price:
                            print(search_text + ": price not found")
                            ok = True
                            break

                        avg_reviews = sum(c['num_of_ratings'] * c['num_of_sold'] for c in candidates_for_price) / len(candidates_for_price)
                        for candidate in candidates_for_price:
                            candidate['weighted_review_score'] = (config.CONFIDENCE_LEVEL * avg_reviews + candidate['num_of_ratings'] * candidate['num_of_sold']) / (config.CONFIDENCE_LEVEL + candidate['num_of_sold'])

                        best_match_for_price = min(candidates_for_price, key=lambda x: x['price'])
                        best_match_for_reviews = max(candidates_for_price, key=lambda x: x['weighted_review_score'])

                        human_behaviour.human_mouse_move(page)
                        human_behaviour.human_pause(page, 2000, 5000)

                        for winner, sort_by in ((best_match_for_price, 'price'), (best_match_for_reviews, 'reviews')):
                            data.append({
                                'product_name': mouse['product_name'],
                                'default_colour': mouse['colour'],
                                'default_skin_id': mouse['skin_id'],
                                'skins': skins_by_product[mouse['product_name']],
                                'link': winner['link'],
                                'sort_by': sort_by,
                            })
                        ok = True
                        break
                    except Exception as e:
                        print(f"{search_text}: attempt {attempt} failed: {type(e).__name__}: {e}")

                if not ok:
                    failed.append(search_text)
                human_behaviour.polite_delay()

            page.close()
            browser.close()
            print(f'1st func: {failed}')
        return data

    # Visits each winning product page once. Its as-loaded state is already
    # the default colour (Shopee opens on the first/default variant, same
    # definition of "default" used going in), so that's read straight off
    # the initial load - then each colour swatch already known in our DB is
    # clicked in turn and the page re-souped, since Shopee swaps price and
    # variant details in place rather than navigating to a new URL. A
    # colour a Shopee listing offers but that isn't already one of this
    # mouse's own DB skins is never clicked or recorded.
    def scrape_shopee_price_from_product_page(self, lst_of_mouse):
        data = []
        failed = []

        with Stealth().use_sync(sync_playwright()) as p:
            browser = p.chromium.launch_persistent_context(**config.BROWSER_LAUNCH, **config.BROWSER_CONTEXT)
            browser.route("**/*",
                lambda route: route.abort()
                if re.search(r"\.(png|jpe?g|gif|webp|svg|avif|woff2?|ttf|mp4)(\?|$)",
                            route.request.url, re.IGNORECASE)
                else route.continue_()
                )
            page = browser.new_page()

            def read_price_and_rating():
                soup = BeautifulSoup(page.content(), 'html.parser')
                price_el = soup.find("div", class_="pyzxvq")
                price_text = price_el.get_text(strip=True) if price_el else ""
                m = re.match(r"([^\d.,]+)\s*([\d.,]+)", price_text)
                currency = m.group(1).strip() if m else '$'
                value = float(m.group(2).replace(",", "")) if m else None

                num_of_stars = 0.0
                for span in soup.find_all("span"):
                    txt = span.get_text(strip=True)
                    if re.fullmatch(r"[0-5](?:\.\d)?", txt):
                        num_of_stars = float(txt)
                        break

                num_ratings_text = None
                ratings_btn = soup.find("div", class_="aEDmfN", string=re.compile("ratings", re.I))
                if ratings_btn:
                    prev = ratings_btn.find_previous_sibling("div", class_="FllsTu")
                    if prev:
                        num_ratings_text = prev.get_text(strip=True)
                num_of_reviews = self.parse_sold(num_ratings_text)

                return soup, currency, value, num_of_stars, num_of_reviews

            for mouse in human_behaviour.shuffled_subset(lst_of_mouse):
                ok = False
                for attempt in range(1, config.MAX_ATTEMPTS_PER_PRODUCT + 1):
                    try:
                        if self.is_blocked(page):
                            print(f"{mouse['product_name']}: looks blocked, sleeping {config.BLOCK_BACKOFF_SECONDS}s")
                            time.sleep(config.BLOCK_BACKOFF_SECONDS)
                            raise RuntimeError("blocked")

                        self._respect_crawl_delay()
                        page.goto(mouse['link'])
                        human_behaviour.human_pause(page, 800, 2000)
                        human_behaviour.human_mouse_move(page)
                        page.evaluate(f"window.scrollBy(0, {random.randint(300, 1000)})")
                        page.wait_for_timeout(timeout=5000)

                        if self.is_blocked(page):
                            print(f"{mouse['product_name']}: looks blocked, sleeping {config.BLOCK_BACKOFF_SECONDS}s")
                            time.sleep(config.BLOCK_BACKOFF_SECONDS)
                            raise RuntimeError("blocked")

                        # colour name (case-insensitive) -> (DB spelling, skin_id)
                        db_colours = {c.lower(): (c, sid) for c, sid in mouse['skins'].items()}

                        def make_row(colour, skin_id, currency, value, num_of_stars, num_of_reviews):
                            return {
                                'skin_id': skin_id,
                                'product_name': mouse['product_name'],
                                'date': datetime.date.today(),
                                'currency': currency,
                                'price': value,
                                'num_of_stars': num_of_stars,
                                'num_of_reviews': num_of_reviews,
                                'colour': colour,
                                'store_link': mouse['link'],
                                'store_name': 'Shopee',
                                'sort_by': mouse['sort_by'],
                            }

                        soup, currency, value, num_of_stars, num_of_reviews = read_price_and_rating()
                        added_colours = set()

                        section = soup.find('section', class_='card')
                        colour_label = None
                        if section:
                            for h2 in section.find_all("h2"):
                                if h2.get_text(strip=True).lower() in ("color", "colour"):
                                    colour_label = h2
                                    break

                        if colour_label is None:
                            # No swatches at all - single-colour listing,
                            # priced as loaded. Only worth a row if that
                            # colour is one of ours.
                            hit = db_colours.get(mouse['default_colour'].lower())
                            if hit:
                                data.append(make_row(hit[0], hit[1], currency, value, num_of_stars, num_of_reviews))
                                added_colours.add(hit[0])
                        else:
                            for btn in colour_label.parent.find_all("button"):
                                aria_label = btn.get("aria-label")
                                colour_text = (aria_label or btn.get_text(strip=True) or "").strip()
                                if not colour_text:
                                    continue

                                hit = db_colours.get(colour_text.lower())
                                if not hit or hit[0] in added_colours:
                                    continue

                                # Already read once above at page-load time -
                                # no need to click a swatch that's already
                                # selected.
                                if colour_text.lower() == mouse['default_colour'].lower():
                                    data.append(make_row(hit[0], hit[1], currency, value, num_of_stars, num_of_reviews))
                                    added_colours.add(hit[0])
                                    continue

                                if aria_label:
                                    locator = page.locator(f'button[aria-label="{aria_label}"]')
                                else:
                                    locator = page.get_by_role("button", name=colour_text, exact=True)
                                locator.first.click(force=True)
                                human_behaviour.human_pause(page, 800, 1800)

                                _, v_currency, v_value, v_stars, v_reviews = read_price_and_rating()
                                data.append(make_row(hit[0], hit[1], v_currency, v_value, v_stars, v_reviews))
                                added_colours.add(hit[0])

                            # Safety net: the default colour's swatch wasn't
                            # found/matched above for some reason (e.g. a
                            # spelling mismatch) - it's still the page's own
                            # as-loaded state, so fall back to that reading.
                            if mouse['default_colour'] not in added_colours:
                                hit = db_colours.get(mouse['default_colour'].lower())
                                if hit:
                                    data.append(make_row(hit[0], hit[1], currency, value, num_of_stars, num_of_reviews))
                                    added_colours.add(hit[0])

                        ok = True
                        break
                    except Exception as e:
                        print(f"{mouse['product_name']}: attempt {attempt} failed: {type(e).__name__}: {e}")

                if not ok:
                    failed.append(mouse)
                human_behaviour.polite_delay()

            page.close()
            browser.close()
            print(f'2nd func: {failed}')
        return data

    def run(self, lst_of_mouse):
        scraper = shopee_new_product_price_scraper()
        search_data = scraper.scrape_shopee_price(lst_of_mouse)
        price_data = scraper.scrape_shopee_price_from_product_page(search_data)
        return price_data

if __name__ == "__main__":
    scraper = shopee_new_product_price_scraper()
    # One dict per skin - 'is_default' marks each mouse's first/lowest-id
    # skin (the only one actually searched); every other skin here just
    # tells phase 2 which colours are ours to match against.
    lst_of_mouse = [
        {'skin_id': 1, 'product_name': "Logitech G502 X", 'colour': "Black", 'is_default': True},
        {'skin_id': 2, 'product_name': "Logitech G502 X", 'colour': "White", 'is_default': False},
    ]
    search_data = scraper.scrape_shopee_price(lst_of_mouse)
    print(search_data)
    price_data = scraper.scrape_shopee_price_from_product_page(search_data)
    print(price_data)
