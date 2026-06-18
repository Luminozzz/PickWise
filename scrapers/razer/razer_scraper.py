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
        print(data)
        return data

    def razer_data_cleaning(self, extracted_data):
        format = {
            'link': None,
            'img_link': None,
            'ergonomy': "none",
            'left_fit': False,
            'battery_life': (0,0),
            'max_DPI': 0,
            'rgb': False,
            'tracking_speed': 0,
            'max_acceleration': 0,
            'polling_rate': (1000, 1000),
            'weight': 0.0,
            'length': 0.0,
            'width': 0.0,
            'height': 0.0,
            'number_of_buttons': 0,
            'bluetooth': False,
            'dongle': False,
            'wired': False,
            'other_features': None
        }
        data = {}
        for detail in extracted_data:
            product_name = detail['product_name']
            feature = detail['feature']
            value = detail['value']

            if product_name not in data:
                data[product_name] = format.copy()
                data[product_name]['brand_name'] = product_name.split(None, 1)[0]

            # default values
            if feature in ["link", "img_link"]:
                data[product_name][feature] = value
                continue
            result = self.extract_feature(feature, value)
            if result is None:
                continue
            items = result if isinstance(result, list) else [result] # Handle single element or list (dimensions)
            print(items)
            for key, val in items:
                if key == 'other_features':
                    if data[product_name][key] is not None:
                        data[product_name][key] = data[product_name][key] + val
                    else:
                        data[product_name][key] = val
                elif isinstance(val, str):
                    if val != "none":
                        data[product_name][key] = val
                elif val > data[product_name][key] and type(val) == type(data[product_name][key]):
                    data[product_name][key] = val
        print(data)
        return data

    def extract_feature(self, feature, value):
        feature = feature.lower()
        value = value.lower()

        if feature in config.RAZER_FORM_FACTOR:
            return [('left_fit', self.left_fit(value)),
                    ('ergonomy', self.ergonomy(value))]
        
        elif feature in config.RAZER_PROGRAMMABLE_BUTTONS:
            return ('number_of_buttons', self.number_of_buttons(value))
        
        elif feature in config.RAZER_CONNECTIVITY:
            return [('bluetooth', self.bluetooth(value)),
                    ('dongle', self.dongle(value)),
                    ('wired', self.wired(value))]
        
        elif feature in config.RAZER_BATTERY_LIFE:
            return ('battery_life', self.battery_life(value))
        
        elif feature in config.RAZER_MAX_DPI:
            return ('max_DPI', self.max_DPI(value))
        
        elif feature in config.RAZER_TRACKING_SPEED:
            return ('tracking_speed', self.tracking_speed(value))
        
        elif feature in config.RAZER_MAX_ACCELERATION:
            return ('max_acceleration', self.max_acceleration(value))
        
        elif feature in config.RAZER_WEIGHT:
            return ('weight', self.weight(value))
        
        elif feature in config.RAZER_SIZE:
            return [('length', self.length(value)), 
                    ('width', self.width(value)), 
                    ('height', self.height(value))]
        
        elif feature in config.RAZER_POLLING_RATE:
            return ('polling_rate', self.polling_rate(value))
        
        elif feature in config.RAZER_RGB:
             return ('rgb', self.rgb(value))
        
        else:
            return ('other_features', str(feature) + ": " + str(value) + '\n')
        
    def ergonomy(self, value: str) -> str:
        match = re.search(r'(\w+)-handed\s*(\w+)', value)
        return match.group(2) if match else "none"
            
    def left_fit(self, value: str) -> str:
        if "left" in value:
             return True
        return False
    
    def number_of_buttons(self, value):
        match = re.search(r'(\d+)', value)
        return int(match.group(1)) if match else 0
                
    def bluetooth(self, value):
        if "bluetooth" in value:
            return True
        return False
            
    def dongle(self, value):
        if "wireless" in value:
            return True
        return False
            
    def wired(self, value):
        if "wired" in value:
            return True
        return False

    def battery_life(self, value: str) -> tuple[int, int]:
        match_month = re.search(r'(\d+)\s*months?', value, re.IGNORECASE)
        if match_month:
            months = int(match_month.group(1)) * 30 * 24
            return (months, months)
                
        match_batt = re.findall(r'(\d+)\s*hours?', value, re.IGNORECASE)
        if match_batt:
            hours = [int(match) for match in match_batt]
            return (min(hours), max(hours))
        return (0,0)
    
    def max_DPI(self, value: str) -> int:
        match = re.search(r'(\d+)', value)
        return int(match.group(1)) if match else 0
    
    def tracking_speed(self, value: str) -> int:
        match = re.search(r'(\d+)', value)
        return int(match.group(1)) if match else 0
    
    def max_acceleration(self, value: str) -> int:
        match = re.search(r'(\d+)', value)
        return int(match.group(1)) if match else 0
    
    def weight(self, value: str) -> float:
        match = re.search(r'(\d+\.?\d*)\s*g', value)
        return float(match.group(1)) if match else 0.0
    
    def length(self, value: str) -> float:
        match = re.search(r'length:\s*(\d+\.?\d*)\s*mm', value)
        return float(match.group(1)) if match else 0.0

    def width(self, value: str) -> float:
        match = re.search(r'width:\s*(\d+\.?\d*)\s*mm', value)
        return float(match.group(1)) if match else 0.0

    def height(self, value: str) -> float:
        match = re.search(r'height:\s*(\d+\.?\d*)\s*mm', value)
        return float(match.group(1)) if match else 0.0
    
    def polling_rate(self, value: str) -> tuple[int, int]:
        match = re.findall(r'(\d+)\s*Hz', value, re.IGNORECASE)
        if match:
            rates = [int(m) for m in match]
            return (1000, max(rates))
        return (1000, 1000)
    
    def rgb(self, value):
        return "none" not in value
        
    def run(self):
        spider = razer_scraper()
        mouse_variation_links = spider.scrape_razer_mouse_variations_links()
        mouse_links = spider.scrape_razer_id_link(mouse_variation_links)
        data = spider.scraper_razer_mouse_details(mouse_links)
        cleaned_data = spider.razer_data_cleaning(data)
        return cleaned_data

if __name__ == "__main__":
    spider = razer_scraper()
    spider.run()