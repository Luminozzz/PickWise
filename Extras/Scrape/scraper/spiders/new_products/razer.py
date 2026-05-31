from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

def scrape_razer_id_link():
    data = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto('https://www.razer.com/ap-en')
        page.wait_for_load_state('networkidle')

        html = page.content()
        

        soup = BeautifulSoup(html, 'html.parser')
        mouse_links = soup.findAll('a', href=re.compile(r'/ap-en/gaming-mice/.+/buy'))
        # This would extract the entire code out, e.g <a href="blabla" class = "blabla"> blabla </a>
        # I just need the href link

        for link in mouse_links:
            url = urljoin('https://www.razer.com/', link['href'])
            page.goto(url)
            page.wait_for_load_state('networkidle', timeout = 50000)
            soup = BeautifulSoup(page.content(), 'html.parser')
            h1 = soup.find('h1', class_='product-name')
            mouse_name = h1.find('a').text.strip()
            final_url = page.url
            url_id = final_url.split('/')[-1]
            data.append({
                'mouse_name': mouse_name,
                'url_id': url_id})
        browser.close()
    return data

    

