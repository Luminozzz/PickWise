import scrapy
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import re
from scrapers import config
from scrapers.image_utils import razer_full_res
from playwright_stealth import Stealth
import unicodedata


class razer_skin_scraper(scrapy.Spider):
    name = "razer_skin_scraper"

    def _current_main_image_src(self, page):
        soup = BeautifulSoup(page.content(), 'html.parser')
        img_div = soup.find('div', class_='product-image')
        img_tag = img_div.find('img', src=re.compile(r'assets3\.razerzone\.com')) if img_div else None
        return img_tag['src'] if img_tag else None

    # For each mouse's own product page, click through every Color/Design
    # option and capture that colour's resulting buy link (the page
    # navigates to a colour-specific SKU URL) and full-res product image.
    # This catches colours/editions that never show up as their own card on
    # the general store listing - e.g. collab editions like "Minecraft
    # Edition" only visible on the plain "Razer Cobra" product page - at the
    # cost of one click+wait per colour instead of a single page parse.
    def scrape_mouse_colour_details(self, lst_of_mouse):
        data = []

        with Stealth().use_sync(sync_playwright()) as p:
            browser = p.chromium.launch_persistent_context(**config.BROWSER_LAUNCH, **config.BROWSER_CONTEXT)
            browser.route(
                "**/*",
                lambda route: route.abort()
                if re.search(r"\.(gif|avif|woff2?|ttf|mp4)(\?|$)",
                            route.request.url, re.IGNORECASE)
                else route.continue_(),
            )
            page = browser.new_page()

            for mouse in lst_of_mouse:
                product_name = mouse['product_name']
                link = mouse['link']
                try:
                    page.goto(link, wait_until='domcontentloaded', timeout=60000)
                    page.wait_for_timeout(2000)

                    # Scoped to the "variant-category-color" selector only,
                    # so the separate "Model" bundle selector (e.g. "Cobra +
                    # Gigantus V2 (Medium)") never gets clicked.
                    colour_buttons = page.locator(
                        'div.bto-variant-selector.variant-category-color '
                        'ul.variant-category-list li.variant-category-list-item button'
                    )
                    count = colour_buttons.count()
                    if count == 0:
                        print(f"[razer_skin_scraper] no colour selector on {product_name}")
                        continue

                    last_img_src = self._current_main_image_src(page)

                    for i in range(count):
                        btn = colour_buttons.nth(i)
                        colour_name = btn.get_attribute('aria-label')
                        if not colour_name:
                            continue
                        colour_name = unicodedata.normalize('NFKD', colour_name).strip()

                        # The already-active swatch (usually the default,
                        # e.g. Black) needs no click - the page already
                        # reflects it. Clicking an already-active swatch
                        # would just re-poll for an image change that will
                        # never come, and time out for no reason.
                        already_active = btn.get_attribute('aria-current') == 'page'
                        if not already_active:
                            # A real Playwright mouse click gets blocked by
                            # CSS layering (the button's own containing <ul>,
                            # and sometimes a cookie-consent overlay). A
                            # JS-level click() bypasses that and still fires
                            # Angular's (click) handler the same way.
                            btn.evaluate('el => el.click()')

                            deadline = time.time() + 8
                            new_src = last_img_src
                            while time.time() < deadline:
                                page.wait_for_timeout(300)
                                new_src = self._current_main_image_src(page)
                                if new_src and new_src != last_img_src:
                                    break
                            else:
                                print(f"[razer_skin_scraper] image never changed for "
                                      f"{product_name} / {colour_name} - keeping it anyway")

                        buy_link = page.url
                        img_src = self._current_main_image_src(page)
                        img_link = razer_full_res(img_src) if img_src else None
                        if img_link is None:
                            continue
                        last_img_src = img_src

                        data.append({
                            'product_name': product_name,
                            'colour': colour_name,
                            'buy_link': buy_link,
                            'img_link': img_link,
                        })
                except Exception as e:
                    print(f"[razer_skin_scraper] failed on {product_name}: {type(e).__name__}: {e}")

            page.close()
            browser.close()
        print(data)
        return data

    def run(self, lst_of_mouse):
        scraper = razer_skin_scraper()
        return scraper.scrape_mouse_colour_details(lst_of_mouse)


if __name__ == "__main__":
    scraper = razer_skin_scraper()
    lst_of_mouse = [{
        'product_name': 'Razer Cobra',
        'link': 'https://www.razer.com/sg-en/gaming-mice/razer-cobra/buy',
    }]
    result = scraper.run(lst_of_mouse)
    print(result)
