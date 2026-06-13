import scrapy
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import random
import time
from scrapers import config
from playwright_stealth import Stealth
from scrapers.human_behaviour import scroll_to_bottom

class logitech_scraper(scrapy.Spider):
    name = "logitech_mouse_spider"
    standard_url = "https://www.logitech.com/en-sg/shop/c/mice"
    urls = {
        #'left_ergo_url': 'https://www.logitech.com/en-sg/shop/c/mice?refine=c_filterhandpreference%3Dleft',
        #'right_ergo_url': 'https://www.logitech.com/en-sg/shop/c/mice?refine=c_filterhandpreference%3Dright',
        #'ambidextrous_url': 'https://www.logitech.com/en-sg/shop/c/mice?refine=c_filterhandpreference%3Dambidextrous',
        'gaming_mouse_url': 'https://www.logitech.com/en-sg/shop/c/mice?refine=c_filterseries%3Dg5-series%7Cg%7Cpro'
    }


    
    # Finding all the mouse variation links, e.g. Viper, Naga, Basilisk and etc
    def scrape_logitech_mouse_id_links(self):
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
            for category, url in self.urls.items():
                page.goto(url)
                page.wait_for_load_state('domcontentloaded',timeout = 100000)
                scroll_to_bottom(page)
                try:
                    page.locator('[data-analytics-title="load-more"]:not([disabled])').wait_for(timeout = 10000)
                    page.evaluate('document.querySelector("[data-analytics-title=\'load-more\']").click()')
                except Exception:
                    print("no button")
                page.wait_for_timeout(timeout = 10000)

                html = page.content()

                soup = BeautifulSoup(html, 'html.parser')
                articles = soup.find_all('article', class_ = ['product-card', 'w-full'])
                for article in articles:
                    name = article.find('h2', class_ = ['brand-title-case', 'product-title']).get_text(strip = True)
                    name_desc = article.find('p').get_text(strip=True)
                    mouse_name = 'Logitech ' + name
                    if category == "gaming_mouse_url":
                        mouse_name = mouse_name + " gaming"
                    img_link = article.find('img', src = re.compile(r'https://resource.logitech.com/w_416'))
                    link = article.find('a', href = re.compile(r'/en-sg/shop/p/'))
                    
                    if link is None or img_link is None:
                        continue
                    url_mouse = urljoin('https://www.logitech.com', link['href'])
                    data_mouse_id[mouse_name] = {'name_desc': None, 'url': None, 'img_link': None, 'left_fit': None}
                    data_mouse_id[mouse_name]['name_desc'] = name_desc
                    data_mouse_id[mouse_name]['url'] = url_mouse
                    data_mouse_id[mouse_name]['img_link'] = img_link['src']
                    data_mouse_id[mouse_name]['hand_fit'] = category
                    
            browser.close()
        print(len(data_mouse_id))
        return data_mouse_id
    
    def is_blocked(self, page):
        try:
            title = page.title().lower()
            body_start = page.content()[:2000].lower()
        except Exception:
            return False
        return any(m in title or m in body_start for m in config.BLOCK_PAGE_MARKERS)
    
    #Cleaning ? and \xa0
    def clean(self, t):
        t = t.replace('\xa0', ' ')
        t = re.sub(r'\s*\?\s*', ' ', t)
        return ' '.join(t.split())
    
    def scraper_logitech_mouse_details(self, mouse_links: dict):
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
            for name, val in mouse_links.items():
                ok = False

                for attempt in range(1,4):  # one retry for transient nav failures
                    
                    try:
                        if self.is_blocked(page):
                            print(f'sleep, wait for {config.BLOCK_BACKOFF_SECONDS}')
                            time.sleep(config.BLOCK_BACKOFF_SECONDS)
                            raise RuntimeError("blocked")
                        
                        print(f"-> {name} (attempt {attempt}): {val['url']}")
                        page.goto(val['url'], wait_until='domcontentloaded', timeout=60000)
                        button = page.locator('[data-analytics-title="specs-open-close"]')
                        print(f"matches: {button.count()}")
                        print(f"visible: {button.first.is_visible() if button.count() else 'N/A'}")
                        button.first.click(force = True)
                        page.wait_for_selector('div.specification', timeout=10000)
                        
                        soup = BeautifulSoup(page.content(), 'html.parser')
                        seen = set()
                        rows_added = 0

                        name_desc_dict = {
                            "product_name": name,
                            "feature": 'name_desc',
                            "value": val['name_desc'],
                        }

                        image_dict = {
                            "product_name": name,
                            "feature": 'img_link',
                            "value": val['img_link'],
                        }

                        link_dict = {
                            "product_name": name,
                            "feature": 'link',
                            "value": val['url'],
                        }

                        hand_fit_dict = {
                            "product_name": name,
                            "feature": 'hand_fit',
                            "value": val['hand_fit'],
                        }

                        data.extend([name_desc_dict, link_dict, image_dict, hand_fit_dict])
                        container = soup.select_one('div.content.svelte-l0ls1x')
                        
                        kv_re = re.compile(r'^\s*(.{1,60}?)\s*:\s*(.+)$', re.DOTALL)

                        
                        # adding dict to data
                        def emit(feature, value):
                            nonlocal rows_added
                            feature = self.clean(feature).rstrip(':')
                            value = self.clean(value)
                            if not feature or not value:
                                return
                            key = (feature, value)
                            if key in seen:
                                return
                            seen.add(key)
                            data.append({'product_name': name, 'feature': feature, 'value': value})
                            rows_added += 1

                        for section in soup.select('div.specification'):
                            title_el = section.find('p')
                            if title_el is None:
                                continue

                            # Skip if its not Dimensions or Technical Specifications
                            if self.clean(title_el.get_text()).lower() not in config.TITLE_WANTED:
                                continue

                            top_lis = [li for li in section.find_all('li') if li.find_parent('li') is None]

                            for top in top_lis:
                                strong = top.find('strong')
                                heading = self.clean(strong.get_text(' ', strip=True)) if strong else None

                                # "Connection Type: Logi Bolt USB Receiver" on the heading line
                                if strong and strong.parent:
                                    head_line = self.clean(strong.parent.get_text(' ', strip=True))
                                    m = kv_re.match(head_line)
                                    if m:
                                        emit(m.group(1), m.group(2))

                                sub_lis = [li for li in top.find_all('li') if not li.find('li')]

                                # if it does not have any headings, it would use the main heading
                                if sub_lis:
                                    for sub in sub_lis:
                                        text = self.clean(sub.get_text(' ', strip=True))
                                        m = kv_re.match(text)
                                        if m:
                                            emit(m.group(1), m.group(2))
                                        elif heading:
                                            emit(heading, text)
                                else:
                                    # plain text without nested list
                                    body = top.get_text(' ', strip=True)
                                    if strong:
                                        body = body.replace(strong.get_text(' ', strip=True), '', 1)
                                    text = self.clean(body)
                                    m = kv_re.match(text)
                                    if m:
                                        emit(m.group(1), m.group(2))
                                    elif heading and text:
                                        emit(heading, text)

                        print(f"   ok - {rows_added} spec rows")
                        ok = True
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
        return data

    
    
    def logitech_data_cleaning(self, extracted_data):
        format = {
            'link': None,
            'img_link': None,
            'ergonomy': "none",
            'left_fit': False,
            'battery_life': (0,0),
            'max_DPI': 0,
            'rgb': False,
            'tracking_speed': None,
            'max_acceleration': None,
            'polling_rate': (125, 125),
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

            if feature in ["link", "img_link"]:
                data[product_name][feature] = value
                continue

            if "gaming" in product_name:
                result = self.extract_feature(feature, value, True)
            else:
                result = self.extract_feature(feature, value, False)

            items = result if isinstance(result, list) else [result] # Handle single element or list (dimensions)
            for key, val in items:
                existing = data[product_name][key]
                if key == 'other_features':
                    data[product_name][key] = (existing + val) if existing is not None else val
                elif isinstance(val, bool):
                    # if existing already returns true, then it will always be true
                    data[product_name][key] = existing or val
                elif isinstance(val, tuple):
                    if val == format[key]:
                        pass
                    elif existing == format[key]:
                        data[product_name][key] = val
                    else:
                        data[product_name][key] = (min(existing[0], val[0]), max(existing[1], val[1]))
                elif isinstance(val, str):
                    if val != "none":
                        data[product_name][key] = val
                elif val is not None and existing is not None and val > existing and type(val) == type(existing):
                    data[product_name][key] = val
        return {name.removesuffix("gaming"): attrs for name, attrs in data.items()}
    
    def helper_other_feature(self, key, parsed, feature, value):
        if parsed is None:
            return ('other_features', f"{feature}: {value}\n")
        return (key, parsed)
    
    def extract_feature(self, feature, value, gaming):
        feature = feature.lower()
        value = value.lower()
        if gaming:
            if any(keyword in feature for keyword in config.LOGITECH_GAMING_FORM_FACTOR):
                return [('left_fit', self.left_fit(value)),
                        ('ergonomy', self.ergonomy(value))]
            
            elif any(keyword in feature for keyword in config.LOGITECH_GAMING_CONNECTIVITY):
                bluetooth = self.bluetooth(value)
                dongle = self.dongle(value)
                wired = self.wired(value)
                if not (bluetooth or dongle or wired):
                    return ('other_features', f"{feature}: {value}\n")
                return [('bluetooth', bluetooth),
                        ('dongle', dongle),
                        ('wired', wired)]
            
            elif any(keyword in feature for keyword in config.LOGITECH_GAMING_PROGRAMMABLE_BUTTONS):
                return self.helper_other_feature('number_of_buttons', self.number_of_buttons(value), feature, value)
            elif any(keyword in feature for keyword in config.LOGITECH_GAMING_BATTERY_LIFE):
                return self.helper_other_feature('battery_life', self.battery_life(value), feature, value)
            elif any(keyword in feature for keyword in config.LOGITECH_GAMING_MAX_DPI):
                return self.helper_other_feature('max_DPI', self.max_DPI(value), feature, value)
            elif any(keyword in feature for keyword in config.LOGITECH_GAMING_TRACKING_SPEED):
                return self.helper_other_feature('tracking_speed', self.tracking_speed(value), feature, value)
            elif any(keyword in feature for keyword in config.LOGITECH_GAMING_MAX_ACCELERATION):
                return self.helper_other_feature('max_acceleration', self.max_acceleration(value), feature, value)
            elif any(keyword in feature for keyword in config.LOGITECH_GAMING_WEIGHT):
                return self.helper_other_feature('weight', self.weight(value), feature, value)
            elif any(keyword in feature for keyword in config.LOGITECH_GAMING_LENGTH):
                return self.helper_other_feature('length', self.length(value), feature, value)
            elif any(keyword in feature for keyword in config.LOGITECH_GAMING_WIDTH):
                return self.helper_other_feature('width', self.width(value), feature, value)
            elif any(keyword in feature for keyword in config.LOGITECH_GAMING_HEIGHT):
                return self.helper_other_feature('height', self.height(value), feature, value)
            elif any(keyword in feature for keyword in config.LOGITECH_GAMING_POLLING_RATE):
                return self.helper_other_feature('polling_rate', self.polling_rate(value), feature, value)
            elif any(keyword in feature for keyword in config.LOGITECH_GAMING_RGB):
                return ('rgb', True)
            else:
                return ('other_features', str(feature) + ": " + str(value) + '\n')
        # Not a gaming Mouse
        else:
            if any(keyword in feature for keyword in config.LOGITECH_FORM_FACTOR):
                return [('left_fit', self.left_fit(value)),
                        ('ergonomy', self.ergonomy(value))]
            
            elif any(keyword in feature for keyword in config.LOGITECH_CONNECTIVITY):
                bluetooth = self.bluetooth(value)
                dongle = self.dongle(value)
                wired = self.wired(value)
                if not (bluetooth or dongle or wired):
                    return ('other_features', f"{feature}: {value}\n")
                return [('bluetooth', bluetooth),
                        ('dongle', dongle),
                        ('wired', wired)]
            
            elif any(keyword in feature for keyword in config.LOGITECH_PROGRAMMABLE_BUTTONS):
                return self.helper_other_feature('number_of_buttons', self.number_of_buttons(value), feature, value)
            elif any(keyword in feature for keyword in config.LOGITECH_BATTERY_LIFE):
                return self.helper_other_feature('battery_life', self.battery_life(value), feature, value)
            elif any(keyword in feature for keyword in config.LOGITECH_MAX_DPI):
                return self.helper_other_feature('max_DPI', self.max_DPI(value), feature, value)
            elif any(keyword in feature for keyword in config.LOGITECH_TRACKING_SPEED):
                return self.helper_other_feature('tracking_speed', self.tracking_speed(value), feature, value)
            elif any(keyword in feature for keyword in config.LOGITECH_MAX_ACCELERATION):
                return self.helper_other_feature('max_acceleration', self.max_acceleration(value), feature, value)
            elif any(keyword in feature for keyword in config.LOGITECH_WEIGHT):
                return self.helper_other_feature('weight', self.weight(value), feature, value)
            elif any(keyword in feature for keyword in config.LOGITECH_LENGTH):
                return self.helper_other_feature('length', self.length(value), feature, value)
            elif any(keyword in feature for keyword in config.LOGITECH_WIDTH):
                return self.helper_other_feature('width', self.width(value), feature, value)
            elif any(keyword in feature for keyword in config.LOGITECH_HEIGHT):
                return self.helper_other_feature('height', self.height(value), feature, value)
            elif any(keyword in feature for keyword in config.LOGITECH_POLLING_RATE):
                return self.helper_other_feature('polling_rate', self.polling_rate(value), feature, value)
            elif any(keyword in feature for keyword in config.LOGITECH_RGB):
                return ('rgb', True)
            else:
                return ('other_features', str(feature) + ": " + str(value) + '\n')

    def ergonomy(self, value: str | None) -> str:
        if "ergo" in value:
            return "ergonomic"
        elif "ambidextrous" in value:
            return "ambidextrous"
        else:
            return "none"
    
    def left_fit(self, value: str) -> str:
        if "left" in value:
             return True
        return False
    
    def number_of_buttons(self, value):
        match = re.search(r'(\d+)', value)
        return int(match.group(1)) if match else None
                
    def bluetooth(self, value):
        if "bluetooth" in value:
            return True
        return None
            
    def dongle(self, value):
        if "usb" in value or "wireless" in value:
            return True
        return None
            
    def wired(self, value):
        if "wired" in value:
            return True
        return None

    def battery_life(self, value: str) -> tuple[int, int]:
        if "month" in value:
            match_month = re.search(r'(\d+)', value, re.IGNORECASE)
            if match_month:
                months = int(match_month.group(1)) * 30 * 24
                return (months, months)
        if "day" in value:
            if match_days:
                match_days = re.search(r'(\d+)', value, re.IGNORECASE)
                days = int(match_days.group(1)) * 24
                return (days, days)
        match_batt = re.findall(r'(\d+)\s*\+?\s*(?:hours?|hrs?|h)\b', value, re.IGNORECASE)
        if match_batt:
            hours = [int(match) for match in match_batt]
            return (min(hours), max(hours))
        return None
    
    def max_DPI(self, value: str) -> int:
        match = re.search(r'(\d+\.?\d*)k', value, re.IGNORECASE)
        if match:
            return int(float(match.group(1)) * 1000)
        match = re.search(r'(\d+)-(\d+)\s+?dpi', value)
        if match:
            return int(match.group(2))
        match = re.search(r'(\d[\d,]*)\s*(?:dpi)?\s*$', value)
        if match:
            return int(match.group(1).replace(',', ''))
        return None
    
    def tracking_speed(self, value: str) -> int:
        match = re.search(r'>(\d+)\s*IPS', value)
        return int(match.group(1)) if match else None
    
    def max_acceleration(self, value: str) -> int:
        match = re.search(r'>(\d+)G', value)
        return int(match.group(1)) if match else None
    
    def weight(self, value: str) -> float:
        match = re.search(r'(\d+\.?\d*)\s*g', value)
        return float(match.group(1)) if match else None
    
    def length(self, value: str) -> float:
        match = re.search(r'(\d+\.?\d*)\s*mm', value)
        return float(match.group(1)) if match else None

    def width(self, value: str) -> float:
        match = re.search(r'(\d+\.?\d*)\s*mm', value)
        return float(match.group(1)) if match else None

    def height(self, value: str) -> float:
        match = re.search(r'(\d+\.?\d*)\s*mm', value)
        return float(match.group(1)) if match else None
    
    def polling_rate(self, value: str) -> tuple[int, int]:
        match = re.findall(r'(\d+)\s*Hz', value, re.IGNORECASE)
        if match:
            rates = [int(m) for m in match]
            if min(rates) == max(rates):
                return (125 , max(rates))
            return (min(rates), max(rates))
        return None
    
    def run(self):
        mouse_id_links = self.scrape_logitech_mouse_id_links()
        data = self.scraper_logitech_mouse_details(mouse_id_links)
        cleaned_data = self.logitech_data_cleaning(data)
        print(cleaned_data)
        return cleaned_data

if __name__  == '__main__':
    spider = logitech_scraper()
    spider.run()
