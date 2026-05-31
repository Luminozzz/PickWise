import scrapy
from scrapy_playwright.page import PageMethod
import csv
from pathlib import Path

class MouseSpider(scrapy.Spider):
    name = "razer_mouse_spider"
    standard_url = "https://www.razer.com/ap-en/gaming-mice/razer/"


    async def start(self):
        current_dir = Path(__file__).parent.parent.parent.parent
        csv_file_path = current_dir / 'raw_data' / 'Razer.csv'
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file) 
            
            for row in reader:
                id = row['url_id']
                url = self.standard_url + id
                yield scrapy.Request(url=url, callback=self.parse, errback=self.handle_error, meta={
                    'product_name': row['product_name'],
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("route", "**/*.{png,jpg,woff,woff2,ttf}",
                            lambda route, _: route.abort()),
                        PageMethod("route", "**/google-analytics*",
                            lambda route, _: route.abort()),
                        PageMethod("route", "**/clarity.ms*",
                            lambda route, _: route.abort()),
                        PageMethod("route", "**/cookieyes*",
                            lambda route, _: route.abort()),
                        PageMethod("route", "**/forter*",
                            lambda route, _: route.abort()),
                        PageMethod("wait_for_load_state", "networkidle"),
                        PageMethod("wait_for_selector", "div.bto-product-specification"),
                        PageMethod("click", "button.btn.btn-link-color.plainBtnText.razer-focus-visible-btn"),
                        PageMethod("wait_for_selector", "div.tech-specs-container"),
                    ],
                })
    
    def handle_error(self, failure):
        self.logger.error(f"FAILED: {failure.request.url} — {failure.value}")
    
    def parse(self, response):

        spec_rows = response.css('ul.product-tech-spec > li.row')

        for row in spec_rows:
            product_name = response.meta.get('product_name')
            feature_name = row.css('div.feature::text').get(default = '').strip()
            raw_values = row.css('div.col-lg-9 *::text').getall()
            cleaned_values = [text.strip() for text in raw_values if text.strip()]

            if feature_name:
                yield {
                    'product_name': product_name,
                    'feature': feature_name,
                    'value': " | ".join(cleaned_values),
                }
