import scrapy
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import random
import time
from scrapers import config
from playwright_stealth import Stealth
import unicodedata

class razer_scraper(scrapy.Spider):
    name = "razer_mouse_spider"
    standard_url = "https://www.razer.com/sg-en/pc/gaming-mice"


    # Finding all the mouse variation links, e.g. Viper, Naga, Basilisk and etc
    def scrape_razer_mouse_variations_links(self):
        data_mouse_variations = []
        
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
            page.goto(self.standard_url)
            page.wait_for_load_state('domcontentloaded',timeout = 100000)

            html = page.content()

            soup = BeautifulSoup(html, 'html.parser')
            opt_1 = soup.find('div', class_ = ['child', 'has-icon']).find_all('a', href = re.compile(r'/sg-en/gaming-mice/'))
            opt_2 = soup.find('div', class_ = ['child', 'has-icon']).find_all('a', href = re.compile(r'/sg-en/pc/gaming-mice/'))
            opt_3 = soup.find('div', class_ = ['child', 'has-icon']).find_all('a', href = re.compile(r'/sg-en/productivity/'))
            mouse_links = opt_1 + opt_2 + opt_3
            #mouse_links.remove("https://www.razer.com/sg-en/gaming-mice/razer-orochi-v2")
            # extracts out all the mouse variation links, e.g. Viper, Naga, Basilisk and etc
            for link in mouse_links :
                url = urljoin('https://www.razer.com/sg-en/gaming-mice/', link['href'])
                data_mouse_variations.append(url)
            browser.close()
        print(data_mouse_variations)
        return data_mouse_variations
    
    def scrape_razer_id_link(self, mouse_variation_links: list):
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
            for mv_link in mouse_variation_links:
                page = browser.new_page()
                try:
                    page.goto(mv_link, timeout = 60000)
                    page.wait_for_load_state('domcontentloaded', timeout = 100000)

                    html = page.content()

                    soup = BeautifulSoup(html, 'html.parser')
                    sections = soup.find_all('section', class_ = ['tile-0', 'tile'])
                    for section in sections:
                        url = section.find('a',href=re.compile(r'/sg-en/gaming-mice/.+/buy'))
                        find_name = section.find('h3').get_text(strip=True)
                        mouse_name = unicodedata.normalize('NFKD', find_name)
                        if url is None or find_name is None:
                            continue
                        data[mouse_name] = {
                            'url_id_1': urljoin('https://www.razer.com/', url['href'])
                        }
                    # mouse_links = soup.find_all('a',href=re.compile(r'/sg-en/gaming-mice/.+/buy'))

                    # # This would extract the entire code out, e.g <a href="blabla" class = "blabla"> blabla </a>
                    # # I just need the href link
                    # for m_link in mouse_links:
                    #     url = urljoin('https://www.razer.com/', m_link['href'])
                    #     page.goto(url, timeout = 60000)
                    #     page.wait_for_load_state('domcontentloaded', timeout = 100000)
                    #     soup = BeautifulSoup(page.content(), 'html.parser')
                    #     h1 = soup.find(['h1', 'h2'], class_='product-name')
                    #     if h1 is None:
                    #         continue
                    #     inner = h1.find(['a', 'h1'])
                    #     mouse_name = (inner or h1).text.strip().title()
                    #     if mouse_name in data:
                    #         continue
                    #     url_id_1 = page.url
                    #     data[mouse_name] = {
                    #         'url_id_1': url_id_1
                    #     }
                finally:
                    page.close()
            browser.close()
        print(data)
        return data

    # Spec element checker, checks for a certain period of time whether an element in the table can be found
    def _expand_specs(self, page, total_timeout=45):
        expand_js = """() => {
            const b = document.querySelector(
                'div.bto-product-specification button.razer-focus-visible-btn');
            if (b) { b.click(); return true; }
            return false;
        }"""

        deadline = time.time() + total_timeout
        while time.time() < deadline:
            # if one element is found, return True
            if page.locator('ul.product-tech-spec > li.row').count() > 0:
                return True
            page.evaluate(expand_js)
            try:
                page.wait_for_selector('ul.product-tech-spec > li.row', timeout=4000)
                return True
            except PlaywrightTimeoutError:
                continue 
        return False
    
    def scraper_razer_mouse_details(self, mouse_links: dict[dict]):
        data = []
        failed = []
        
        block_resources = re.compile(
            r"\.(png|jpe?g|gif|webp|svg|avif|woff2?|ttf|mp4)(\?|$)"
            r"|google-analytics|googletagmanager|clarity\.ms|forter"
            r"|doubleclick|facebook|hotjar",
            re.IGNORECASE,
        )

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

            for name, link in mouse_links.items():
                url = link['url_id_1']
                ok = False

                for attempt in (1, 2):  # one retry for transient nav failures
                    
                    try:
                        print(f"-> {name} (attempt {attempt}): {url}")
                        page.goto(url, wait_until='domcontentloaded', timeout=60000)
                        page.wait_for_selector('div.bto-product-specification', timeout=45000)
                        soup = BeautifulSoup(page.content(), 'html.parser')
                        img_link = soup.find('div', class_ = "product-image").find('img', src = re.compile(r'https://assets3.razerzone.com/'))
                        if not self._expand_specs(page):
                            raise RuntimeError("spec list never appeared after expanding")
                        soup = BeautifulSoup(page.content(), 'html.parser')
                        seen = set()
                        rows_added = 0
                        # price_ele = soup.find("span", class_ = ["final-price", "text_white"])
                        # price = "".join(price_ele.find_all(string=True, recursive=True)).strip()
                        # value = re.search(r'[\d.]+', price).group()
                        
                        append_data = [{
                            'product_name': name,
                            'feature': 'link',
                            'value': url,
                        },
                        {
                            'product_name': name,
                            'feature': 'img_link',
                            'value': img_link['src'],
                        }]
                        print(append_data)
                        data.extend(append_data)
                        print(data)
                        for row in soup.select('ul.product-tech-spec > li.row'):
                            feat_el = row.select_one('div.feature')
                            val_el = row.select_one('div.col-lg-9')

                            if feat_el is None or val_el is None:
                                continue
                            feature = feat_el.get_text(strip=True)
                            value = " | ".join(val_el.stripped_strings)
                            key = (feature, value)
                            if not feature or key in seen:
                                continue
                            seen.add(key)
                            data.append({
                                'product_name': name,
                                'feature': feature,
                                'value': value,
                            })
                            rows_added += 1
                        print(f"   ok - {rows_added} spec rows")
                        ok = True
                        break  # success - stop retrying

                    except Exception as e:
                        print(f"   attempt {attempt} failed: {type(e).__name__}: {e}")
                if not ok:
                    failed.append(name)
            page.close()
            browser.close()

        if failed:
            print(f"\n{len(failed)} product(s) failed: {failed}")
        return data

    def run(self):
        spider = razer_scraper()
        mouse_variation_links = spider.scrape_razer_mouse_variations_links()
        mouse_links = spider.scrape_razer_id_link(mouse_variation_links)
        data = spider.scraper_razer_mouse_details(mouse_links)
        return data

if __name__ == "__main__":
    spider = razer_scraper()
    mouse_variation_links = spider.scrape_razer_mouse_variations_links()
    mouse_links = spider.scrape_razer_id_link(mouse_variation_links)
    data = spider.scraper_razer_mouse_details(mouse_links)
    print(data)