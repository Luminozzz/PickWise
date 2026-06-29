import scrapy
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import random
import time
from scrapers import config
from scrapers.image_utils import razer_full_res
from playwright_stealth import Stealth
import unicodedata

class razer_skin_scraper(scrapy.Spider):
    name = "razer_skin_scraper"
    store_url = "https://www.razer.com/sg-en/store/gaming-mice"

    # List of dictionary. Each element contains the id, brand_name, product_name, link
    def scrape_razer_mouse_colours(self, lst_of_mouse):
        data = []

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
                    page.goto(mouse['link'], wait_until="domcontentloaded", timeout = 60000)

                    soup = BeautifulSoup(page.content(), 'html.parser')
                    uls = soup.find('div', class_ = "variant-category-color")
                    if uls is None:
                        temp = {
                            'product_name': mouse['product_name'],
                            'colour': 'Black',
                        }
                        data.append(temp)
                        continue
                    for li in uls.find_all('li'):
                        ok = li.find('span', class_ = 'no-discount')
                        if ok is not None:
                            if ok.text.strip() != "":
                                continue
                        colours = li.find_all('span', class_ = 'bto-category-label-info')
                        if colours is None:
                            continue
                        for colour in colours:
                            colour = colour.text.strip()
                            temp = {
                                'product_name': mouse['product_name'],
                                'colour': colour,
                            }
                            data.append(temp)
                except Exception as e:
                    print(f"Error processing {mouse['product_name']}: {e}")
            page.close()
            browser.close()
        return data

    def scrape_img_link(self, colour_data):
        data = []

        with Stealth().use_sync(sync_playwright()) as p:
            browser = p.chromium.launch_persistent_context(**config.BROWSER_LAUNCH, **config.BROWSER_CONTEXT)
            page = browser.new_page()
            try:
                page.goto(self.store_url)
                page.wait_for_selector('div.card-wrapper-main', timeout = 60000)
                soup = BeautifulSoup(page.content(), 'html.parser')
                all_the_divs = soup.find_all('div', class_ = 'card-wrapper-main')
                for mouse in colour_data:
                    colour = mouse['colour']
                    product_name = mouse['product_name']
                    # Find the card whose title matches this product. If none
                    # matches, skip — never fall back to a stale/last div, which
                    # would attribute another product's image to this mouse.
                    spec_div = None
                    for div in all_the_divs:
                        if div.find('h3', string = product_name) is not None:
                            spec_div = div
                            break
                    if spec_div is None:
                        continue
                    colour_options = spec_div.find('ul', class_ = ['options-colordesign', 'options'])
                    if colour_options is None:
                        img_link = spec_div.find('div', class_ = 'thumbnail-holder').find('img')
                        if img_link is None:
                            continue
                        temp = {
                            'product_name': product_name,
                            'colour': colour,
                            'img_link': razer_full_res(img_link['src'])
                        }
                        data.append(temp)
                        continue
                    img_link = colour_options.find(attrs={'data-value': colour})
                    if img_link is None:
                        continue
                    temp = {
                        'product_name': product_name,
                        'colour': colour,
                        'img_link': razer_full_res(img_link['data-thumbnail'])
                    }
                    data.append(temp)
            except Exception as e:
                print(f"Error processing {mouse['product_name']}: {e}")
            page.close()
            browser.close()
        return data

    def run(self,lst_of_mouse):
        scraper = razer_skin_scraper()
        mouse_colours = scraper.scrape_razer_mouse_colours(lst_of_mouse)
        mouse_links = scraper.scrape_img_link(mouse_colours)
        return mouse_links
