from pydoc import text
import scrapy
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import random
import datetime
from rapidfuzz import fuzz
from scrapers import config
from playwright_stealth import Stealth
from scrapers import human_behaviour

class amazon_existing_product_price_scraper(scrapy.Spider):
    name = "amazon_existing_product_price_scraper"
    amazon_store_url = "https://www.amazon.sg/"

    def scrape_amazon_price_from_product_page(self, lst_of_mouse):
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
            for mouse in human_behaviour.shuffled_subset(lst_of_mouse):
                try:
                    page.goto(mouse['store_link'])
                    page.evaluate(f"window.scrollBy(0, {random.randint(300, 1000)})")
                    page.wait_for_selector('span.a-price', state = "visible", timeout = 60000)

                    html = page.content()
                    soup = BeautifulSoup(html, 'html.parser')

                    page.wait_for_timeout(random.randint(2000, 5000))
                    price_with_currency = soup.find('span', class_ = 'a-price').find('span', class_ = 'a-offscreen').text.strip()
                    
                    m_cur = re.match(r"^[^\d\s]+", price_with_currency)
                    currency = m_cur.group(0) if m_cur else None
                    m_num = re.search(r"\d[\d,]*(?:\.\d+)?", price_with_currency)
                    value = float(m_num.group(0).replace(",", "")) if m_num else None

                    colour = soup.find('table', class_ = 'a-normal', attrs={'role': 'list'})
                    if colour is None:
                        colour = None
                    else:
                        colour_row = colour.find('tr', class_='po-color')
                        colour = colour_row.find('span', class_='po-break-word').text.strip() if colour_row else None
                    data.append({
                        'product_name': mouse['product_name'],
                        'date': datetime.date.today(),
                        'currency': currency,
                        'price': value,
                        'colour': colour,
                        'store_link': mouse['store_link'],
                        'store_name': 'Amazon'     
                    })
                except Exception as e:
                    print(f"failed: {type(e).__name__}: {e}")
                    failed.append(mouse)
            page.close()
            browser.close()
            print(failed)
        return data
    
    def run(self, lst_of_mouse):
        scraper = amazon_existing_product_price_scraper()
        price_data = scraper.scrape_amazon_price_from_product_page(lst_of_mouse)
        return price_data