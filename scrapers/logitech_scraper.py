import scrapy
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import random
import time
from scrapers import config
from playwright_stealth import Stealth

class logitech_scraper(scrapy.Spider):
    name = "logitech_mouse_spider"
    standard_url = "https://www.logitech.com/en-sg/shop/c/mice"


    def scroll_to_bottom(self, page):
        last_position = page.evaluate("window.scrollY")
        while True:
            page.evaluate(f"window.scrollBy(0, {random.randint(300, 1000)})")
            page.wait_for_timeout(1300)

            current_position = page.evaluate("window.scrollY")
            if current_position == last_position:
                break
            last_position = current_position
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
            page.goto(self.standard_url)
            page.wait_for_load_state('domcontentloaded',timeout = 100000)
            page.locator('[data-analytics-title="load-more"]:not([disabled])').wait_for(timeout = 60000)
            self.scroll_to_bottom(page)
            page.evaluate('document.querySelector("[data-analytics-title=\'load-more\']").click()')
            page.wait_for_timeout(timeout = 10000)

            html = page.content()

            soup = BeautifulSoup(html, 'html.parser')
            articles = soup.find_all('article', class_ = ['product-card', 'w-full'])
            
            for article in articles:
                name = article.find('h2', class_ = ['brand-title-case', 'product-title']).get_text(strip = True)
                mouse_name = 'Logitech ' + name
                img_link = article.find('img', src = re.compile(r'https://resource.logitech.com/w_416'))
                link = article.find('a', href = re.compile(r'/en-sg/shop/p/'))
                
                if link is None or img_link is None:
                    continue
                url = urljoin('https://www.logitech.com', link['href'])
                data_mouse_id[mouse_name] = {'url': None, 'img_link': None}
                data_mouse_id[mouse_name]['url'] = url
                data_mouse_id[mouse_name]['img_link'] = img_link['src']
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
            for name, link in mouse_links.items():
                ok = False

                for attempt in range(1,4):  # one retry for transient nav failures
                    
                    try:
                        if self.is_blocked(page):
                            print(f'sleep, wait for {config.BLOCK_BACKOFF_SECONDS}')
                            time.sleep(config.BLOCK_BACKOFF_SECONDS)
                            raise RuntimeError("blocked")
                        print(f"-> {name} (attempt {attempt}): {link['url']}")
                        page.goto(link['url'], wait_until='domcontentloaded', timeout=60000)
                        #page.wait_for_selector('[data-analytics-title="specs-open-close"]', timeout=30000, state='visible',)
                        #page.locator('[data-analytics-title="specs-open-close"]').click(force = True)
                        button = page.locator('[data-analytics-title="specs-open-close"]')
                        print(f"matches: {button.count()}")
                        print(f"visible: {button.first.is_visible() if button.count() else 'N/A'}")
                        page.locator('[data-analytics-title="specs-open-close"]').click()
                        #page.get_by_role('button', name = re.compile(r'specs and compatibility', re.IGNORECASE)).click(force=True)
                        page.wait_for_selector('div.specification', timeout=10000)
                        #if not self._expand_specs(page):
                        #    raise RuntimeError("spec list never appeared after expanding")
                        
                        soup = BeautifulSoup(page.content(), 'html.parser')
                        seen = set()
                        rows_added = 0

                        image_dict = {
                            "product_name": name,
                            "feature": 'img_link',
                            "value": link['img_link'],
                        }
                        link_dict = {
                            "product_name": name,
                            "feature": 'link',
                            "value": link['url'],
                        }
                        data.extend([link_dict, image_dict])
                        container = soup.select_one('div.content.svelte-l0ls1x')
                        print([d.get("class") for d in soup.select("div.content")])
                        for li in container.select("ul.specs-list > li"):
                            strong = li.find("strong")
                            span = li.find("span", class_="font-light")
                            if not (strong and span):
                                continue
                            feature = strong.get_text(strip=True).rstrip(":").strip()
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
                        
                        kv_re = re.compile(r"(.+?):\s*(.+)")
                        for li in container.select("li"):
                            if li.find("ul") or li.find("strong") or li.find("span"):
                                continue
                            text = li.get_text(strip=True)
                            m = kv_re.match(text)
                            if not m:
                                continue
                            feature, value = m.group(1).strip(), m.group(2).strip()
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
            print(data)

        if failed:
            print(f"\n{len(failed)} product(s) failed: {failed}")
        print(data)
        return data

    def run(self):
        mouse_id_links = self.scrape_logitech_mouse_id_links()
        data = self.scraper_logitech_mouse_details(mouse_id_links)
        return data

if __name__  == '__main__':
    spider = logitech_scraper()
    spider.run()
