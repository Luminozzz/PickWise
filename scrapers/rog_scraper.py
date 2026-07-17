import scrapy
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import random
import time
from scrapers import config
from playwright_stealth import Stealth

class rog_scraper(scrapy.Spider):
    name = "rog_mouse_spider"
    #change location
    standard_symmetrical_url = "https://rog.asus.com/my/mice-mouse-pads/mice-series/?items=51008"
    standard_ergonomic_url = "https://rog.asus.com/my/mice-mouse-pads/mice-series/?items=51009"

    def scroll_to_bottom(self, page):
        last_position = page.evaluate("window.scrollY")
        while True:
            page.evaluate(f"window.scrollBy(0, {random.randint(300, 1000)})")
            page.wait_for_timeout(1300)

            current_position = page.evaluate("window.scrollY")
            if current_position == last_position:
                break
            last_position = current_position
            
    def scrape_rog_mouse_id_links(self, url: str):
        data_mouse_id = {}
        
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
            page.goto(url)
            page.wait_for_load_state('networkidle',timeout = 100000)
            self.scroll_to_bottom(page)
            page.wait_for_load_state('networkidle',timeout = 100000)
            
            html = page.content()

            soup = BeautifulSoup(html, 'html.parser')
            divs = soup.find_all('div', class_ = 'ProductResultItem__productItem__Wc51h')
            
            for div in divs:
                mouse_name = div.find('span', class_ = 'ProductResultItem__mktName__bqftk').get_text(strip = True)
                print(mouse_name)
                link = div.find('a', href = re.compile(r'https://rog.asus.com/my/mice-mouse-pads/mice/'))
                print(link)
                img_link = div.find('picture', class_ = "ProductResultItem__show__K8KZO").find('img', src = re.compile(r"https://dlcdnwebimgs.asus.com/gain/"))
                if link is None or img_link is None:
                    continue
                data_mouse_id[mouse_name] = {'link': None, 'img_link': None}
                data_mouse_id[mouse_name]['link'] = link['href'] + "spec/"
                data_mouse_id[mouse_name]['img_link'] = img_link['src']
            browser.close()
        print(len(data_mouse_id))
        return data_mouse_id
    

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
    
    def scraper_rog_mouse_details(self, mouse_links: dict):
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
            for name, links in mouse_links.items():
                ok = False

                for attempt in range(1,4):  # one retry for transient nav failures
                    
                    try:
                        if self.is_blocked(page):
                            print(f'sleep, wait for {config.BLOCK_BACKOFF_SECONDS}')
                            time.sleep(config.BLOCK_BACKOFF_SECONDS)
                            raise RuntimeError("blocked")
                        print(f"-> {name} (attempt {attempt}): {links['link']}")
                        page.goto(links['link'], wait_until='domcontentloaded', timeout=60000)
                        
                        soup = BeautifulSoup(page.content(), 'html.parser')
                        seen = set()
                        rows_added = 0
                        container = soup.find_all('div', class_ = 'ProductSpecSingle__singleSpecGridRow__+afIj')
                        for div in container:
                            h2 = div.find('h2', class_ = 'ProductSpecSingle__productSpecItemTitle__HKAZq')
                            span = div.find("span", class_="ProductSpecSingle__descriptionItemValue__IVzBl")
                            if not (h2 and span):
                                continue
                            feature = h2.get_text(strip=True)
                            value = span.get_text(strip=True)
                            key = (feature, value)
                            if not feature or key in seen:
                                continue
                            seen.add(key)
                            data.append({
                                "product_name": name,
                                "feature": feature,
                                "value": value,
                            })
                            rows_added += 1
                        print(f"   ok - {rows_added} spec rows")
                        ok = True
                        print(data)
                        break  # success - stop retrying

                    except Exception as e:
                        print(f"   attempt {attempt} failed: {type(e).__name__}: {e}")
                delay = random.uniform(30, 45)
                if random.random() < 0.1:
                    delay = random.uniform(90, 150)
                time.sleep(delay)
                if not ok:
                    failed.append(name)
            page.close()
            browser.close()

        if failed:
            print(f"\n{len(failed)} product(s) failed: {failed}")
        print(data)
        print(len(data))
        return data

    def run(self):
        ergo_mouse_id_links = self.scrape_rog_mouse_id_links(self.standard_ergonomic_url)
        ergo_data = self.scraper_rog_mouse_details(ergo_mouse_id_links)
        symm_mouse_id_links = self.scrape_rog_mouse_id_links(self.standard_symmetrical_url)
        symm_data = self.scraper_rog_mouse_details(symm_mouse_id_links)
        data = {'ergo': ergo_data, 'symm': symm_data}
        print(data)
        return data

if __name__  == '__main__':
    spider = rog_scraper()
    spider.run()
