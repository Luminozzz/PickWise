import scrapy
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import random
import time
import datetime
from scrapers import config
from playwright_stealth import Stealth
import unicodedata

class razer_price_scraper(scrapy.Spider):
    name = "razer_price_scraper"

    # List of dictionary. Each element contains the product_name, link
    def scrape_razer_mouse_price(self, lst_of_mouse):
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
                try:
                    page.goto(mouse['link'], timeout = 60000)
                    page.wait_for_load_state('domcontentloaded', timeout = 60000)

                    html = page.content()
                    soup = BeautifulSoup(html, 'html.parser')

                    div = soup.find('div', class_ = 'col-product-price')
                    if div is None:
                        continue
                    price_ele = div.find('span', class_ = 'final-price')
                    if price_ele is None:
                        continue
                    price_with_currency = price_ele.text.strip()
                    print(price_with_currency)
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
                        'store_name': 'Razer official store',
                        'sort_by': 'official'
                    })
                except Exception as e:
                    print(f"failed: {type(e).__name__}: {e}")
                    failed.append(mouse)
            page.close()
            browser.close()
            print(f'1st func: {failed}')
        return data
    
    def run(self, lst_of_mouse):
        scraper = razer_price_scraper()
        price_data = scraper.scrape_razer_mouse_price(lst_of_mouse)
        return price_data
    

if __name__ == "__main__":
    scraper = razer_price_scraper()
    lst_of_mouse = [{
        'product_name': 'Razer Cobra Pro',
        'link': 'https://www.razer.com/sg-en/gaming-mice/razer-cobra-pro/buy'
    }]
    search_data = scraper.scrape_razer_mouse_price(lst_of_mouse)
    print(search_data)