import scrapy
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import re
import time
import datetime
from scrapers import config
from playwright_stealth import Stealth
from scrapers import human_behaviour

class hp_price_scraper(scrapy.Spider):
    name = "hp_price_scraper"

    def is_blocked(self, page):
        try:
            title = page.title().lower()
            body_start = page.inner_text("body")[:2000].lower()
        except Exception:
            return False
        return any(m in title or m in body_start for m in config.BLOCK_PAGE_MARKERS)

    def _goto_with_block_check(self, page, url, **kwargs):
        for attempt in range(1, config.MAX_ATTEMPTS_PER_PRODUCT + 1):
            page.goto(url, **kwargs)
            if not self.is_blocked(page):
                return True
            print(f"[hp_price_scraper] blocked at {url} (attempt {attempt}/{config.MAX_ATTEMPTS_PER_PRODUCT})")
            if attempt < config.MAX_ATTEMPTS_PER_PRODUCT:
                print(f"[hp_price_scraper] sleeping {config.BLOCK_BACKOFF_SECONDS}s before retry")
                time.sleep(config.BLOCK_BACKOFF_SECONDS)
        print(f"[hp_price_scraper] WARNING: giving up on {url} - still blocked after {config.MAX_ATTEMPTS_PER_PRODUCT} attempts")
        return False

    # List of dictionary. Each element contains the product_name, link, colour
    def scrape_hp_mouse_price(self, lst_of_mouse):
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
            for mouse in lst_of_mouse:
                ok = False
                for attempt in range(1, config.MAX_ATTEMPTS_PER_PRODUCT + 1):
                    try:
                        if not self._goto_with_block_check(page, mouse['link'], wait_until='domcontentloaded', timeout=config.PAGE_NAV_TIMEOUT):
                            raise RuntimeError("blocked")
                        page.wait_for_selector('div.price-box.price-final_price', timeout=config.SPEC_WAIT_TIMEOUT)
                        page.wait_for_timeout(1500)

                        soup = BeautifulSoup(page.content(), 'html.parser')
                        price_elem = soup.select_one('div.price-box.price-final_price span.price')
                        if price_elem is None:
                            raise RuntimeError("price not found")
                        price_with_currency = price_elem.get_text(strip=True)

                        m_cur = re.search(r"[^\d\s]+(?=\d)", price_with_currency)
                        currency = m_cur.group(0) if m_cur else None
                        m_num = re.search(r"\d[\d,]*(?:\.\d+)?", price_with_currency)
                        value = float(m_num.group(0).replace(",", "")) if m_num else None

                        data.append({
                            'product_name': mouse['product_name'],
                            'date': datetime.date.today(),
                            'currency': currency,
                            'price': value,
                            'num_of_stars': None,
                            'num_of_reviews': None,
                            'colour': mouse['colour'],
                            'store_link': mouse['link'],
                            'store_name': 'HP official store',
                            'sort_by': 'official'
                        })
                        ok = True
                        break
                    except Exception as e:
                        print(f"{mouse['product_name']}: attempt {attempt} failed: {type(e).__name__}: {e}")
                if not ok:
                    failed.append(mouse)
                human_behaviour.polite_delay()

            page.close()
            browser.close()
            print(f'failed: {failed}')
        return data

    def run(self, lst_of_mouse):
        scraper = hp_price_scraper()
        price_data = scraper.scrape_hp_mouse_price(lst_of_mouse)
        return price_data


if __name__ == "__main__":
    scraper = hp_price_scraper()
    lst_of_mouse = [{
        'product_name': 'HP 400 Quiet Wireless Mouse, Maple',
        'link': 'https://www.hp.com/sg-en/shop/hp-400-quiet-wireless-mouse-az7b6aa.html',
        'colour': 'Maple'
    }]
    print(scraper.scrape_hp_mouse_price(lst_of_mouse))
