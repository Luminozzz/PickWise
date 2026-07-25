import scrapy
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import re
import time
import datetime
from scrapers import config
from playwright_stealth import Stealth
from scrapers import human_behaviour

class logitech_price_scraper(scrapy.Spider):
    name = "logitech_price_scraper"

    def is_blocked(self, page):
        try:
            title = page.title().lower()
            body_start = page.inner_text("body")[:2000].lower()
        except Exception:
            return False
        return any(m in title or m in body_start for m in config.BLOCK_PAGE_MARKERS)

    # List of dictionary. Each element contains the product_name, link, colour
    def scrape_logitech_mouse_price(self, lst_of_mouse):
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
                        if self.is_blocked(page):
                            print(f"sleep, wait for {config.BLOCK_BACKOFF_SECONDS}")
                            time.sleep(config.BLOCK_BACKOFF_SECONDS)
                            raise RuntimeError("blocked")

                        page.goto(mouse['link'], wait_until='domcontentloaded', timeout=config.PAGE_NAV_TIMEOUT)
                        # The main product price - not to be confused with the
                        # "font-bold" priced cards further down the page for
                        # unrelated recommended products.
                        page.wait_for_selector('div.heading4', timeout=config.SPEC_WAIT_TIMEOUT)
                        page.wait_for_timeout(2000)

                        soup = BeautifulSoup(page.content(), 'html.parser')
                        price_elem = soup.select_one('div.heading4')
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
                            'store_name': 'Logitech official store',
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
        scraper = logitech_price_scraper()
        price_data = scraper.scrape_logitech_mouse_price(lst_of_mouse)
        return price_data


if __name__ == "__main__":
    scraper = logitech_price_scraper()
    lst_of_mouse = [{
        'product_name': 'Logitech Signature M650',
        'link': 'https://www.logitech.com/en-sg/shop/p/m650-signature-wireless-mouse',
        'colour': 'Black'
    }]
    print(scraper.scrape_logitech_mouse_price(lst_of_mouse))
