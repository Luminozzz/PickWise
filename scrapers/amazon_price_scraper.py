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

class amazon_new_product_price_scraper(scrapy.Spider):
    name = "amazon_new_product_price_scraper"
    amazon_store_url = "https://www.amazon.sg/"

    # List of dictionary. Each element contains the product_name
    def scrape_amazon_price(self, lst_of_mouse):
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
                    product_pool = []
                    search_url = self.amazon_store_url + "s?k=" + "+".join(mouse.split(" "))
                    page.goto(search_url)
                    human_behaviour.human_pause(page, 800, 2000)
                    human_behaviour.human_mouse_move(page)   
                    human_behaviour.human_scroll(page)
                    page.evaluate(f"window.scrollBy(0, {random.randint(300, 1000)})")
                    page.wait_for_selector('div[role="listitem"]', state = "visible", timeout=60000)
                    page.wait_for_timeout(timeout=7000)
                    human_behaviour.human_pause(page, 1500, 4000)
                    human_behaviour.human_mouse_move(page)  
                    html = page.content()
                    soup = BeautifulSoup(html, 'html.parser')

                    # Find the first n products with the minimum price out of the n
                    divs = soup.find_all('div', attrs={'role': 'listitem'}, limit=config.NUMBER_OF_PRODUCTS_COMPARISON)
                    for div in divs:
                        title_elem = div.find('div', attrs = {'data-cy': 'title-recipe'}).find('a', recursive=False).find('span')
                        price_elem = div.find('div', attrs={'data-cy': 'price-recipe'}).find('span', class_ = 'a-offscreen')
                        
                        if title_elem is None:
                            continue

                        title = title_elem.text.strip()
                        clean_title = re.search(r'(.+?)(?:\s*[-,]\s*)',title).group(1).strip() if re.search(r'(.+?)(?:\s*[-,]\s*)',title) else title.strip()
                        price = float(re.search(r"\d[\d,]*(?:\.\d+)?", price_elem.text.strip()).group(0).replace(",", "")) if price_elem else None

                        num_of_ele = len(mouse.split()) + config.NUMBER_OF_EXTRA_WORDS
                        clean_title = " ".join((clean_title.split())[:num_of_ele])
                        score = fuzz.WRatio(mouse, clean_title)
                        ASIN = div['data-asin']
                        product_pool.append({
                            'title': title,
                            'clean_title': clean_title,
                            'ASIN': ASIN,
                            'price': price,
                            'score': score
                        })
                    max_score = max(product_pool, key = lambda x: x['score'])['score']

                    for product in product_pool:
                        product['score_diff'] = max_score - product['score']

                    exact_words = mouse.lower().split()[1:]
                    candidates_for_price = [p for p in product_pool if p['score_diff'] <= 3 and all(word in p['clean_title'].lower().split() for word in exact_words) and p['price'] is not None]
                    if not candidates_for_price:
                        continue

                    best_match = min(candidates_for_price, key = lambda x: x['price'])
                    
                    human_behaviour.human_mouse_move(page)
                    human_behaviour.human_pause(page, 2000, 5000)
                    data.append({
                        'product_name': mouse,
                        'ASIN': best_match['ASIN'],
                        'link': f'https://www.amazon.sg/dp/{best_match["ASIN"]}',
                        'price': best_match['price']
                    })
                except Exception as e:
                    print(f"failed: {type(e).__name__}: {e}")
                    failed.append(mouse)

            page.close()
            browser.close()
            print(failed)
        return data
    
    def scrape_amazon_price_from_product_page(self, lst_of_mouse):
        data = []
        extra = []
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
                    page.goto(mouse['link'])
                    page.evaluate(f"window.scrollBy(0, {random.randint(300, 1000)})")
                    page.wait_for_selector('span.a-price', state = "visible", timeout = 60000)

                    html = page.content()
                    soup = BeautifulSoup(html, 'html.parser')

                    variant_exists = soup.find('div#inline-twister-row-color_name')
                    if variant_exists:
                        variant_lis = variant_exists.find_all('li')
                        for variant in variant_lis:
                            if variant['data-asin'] != mouse['ASIN']:
                                extra.append({
                                    'product_name': mouse['product_name'],
                                    'ASIN': variant['data-asin'],
                                    'link': f'https://www.amazon.sg/dp/{variant["data-asin"]}',
                                })

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
                        'store_link': mouse['link'],
                        'store_name': 'Amazon'     
                    })
                # if other variant exists
                    if extra:
                        for mouse in extra:
                            page.goto(mouse['link'])
                            human_behaviour.human_pause(page, 800, 2000)
                            human_behaviour.human_mouse_move(page)
                            human_behaviour.human_scroll(page) 
                            page.wait_for_selector('span.a-price', state = "visible", timeout = 60000)
                            page.wait_for_selector('table.a-normal', state = "visible", timeout = 60000)
                            human_behaviour.human_hover(page, 'span.a-price')      # <-- hover the price like you're inspecting it
                            human_behaviour.human_pause(page, 1000, 3000)

                            html = page.content()
                            soup = BeautifulSoup(html, 'html.parser')

                            price_with_currency = soup.find('span', class_ = 'a-price').find('span', class_ = 'a-offscreen').text.strip()
                            
                            m_cur = re.match(r"^[^\d\s]+", price_with_currency)
                            currency = m_cur.group(0) if m_cur else None
                            m_num = re.search(r"\d[\d,]*(?:\.\d+)?", price_with_currency)
                            value = float(m_num.group(0).replace(",", "")) if m_num else None

                            colour = soup.find('table', class_ = 'a-normal')
                            print(colour)
                            if colour is None:
                                colour = None
                            else:
                                colour = colour.find('tr', class_ = 'po-color').find('span', class_ = 'po-break-word').text.strip()
                            data.append({
                                'product_name': mouse['product_name'],
                                'date': datetime.date.today(),
                                'currency': currency,
                                'price': value,
                                'colour': colour,
                                'store_link': mouse['link'],
                                'store_name': 'Amazon'     
                            })
                            human_behaviour.human_mouse_move(page)
                            human_behaviour.human_pause(page, 2000, 5000)
                except Exception as e:
                    print(f"failed: {type(e).__name__}: {e}")
                    failed.append(mouse)
            page.close()
            browser.close()
            print(failed)
        return data

    def run(self, lst_of_mouse):
        scraper = amazon_new_product_price_scraper()
        search_data = scraper.scrape_amazon_price(lst_of_mouse)
        price_data = scraper.scrape_amazon_price_from_product_page(search_data)
        return price_data

if __name__ == "__main__":
    scraper = amazon_new_product_price_scraper()
    lst_of_mouse = ["Logitech G502 LIGHTSPEED", "Logitech G502", "Logitech G502 X"]
    search_data = scraper.scrape_amazon_price(lst_of_mouse)
    price_data = scraper.scrape_amazon_price_from_product_page(search_data)




            

