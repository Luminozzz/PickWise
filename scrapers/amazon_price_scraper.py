from pydoc import text
import scrapy
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import random
import datetime
import time
from rapidfuzz import fuzz
from scrapers import config
from playwright_stealth import Stealth
from scrapers import human_behaviour

class amazon_new_product_price_scraper(scrapy.Spider):
    name = "amazon_new_product_price_scraper"
    amazon_store_url = "https://www.amazon.sg/"

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
                # is_default means this mouse only ships in one colour (no
                # distinct buy link of its own) - leave colour out of the
                # search text rather than searching on an arbitrary/
                # unconfirmed colour name.
                if mouse.get('is_default'):
                    search_text = mouse['product_name'].strip()
                else:
                    search_text = f"{mouse['product_name']} {mouse['colour']}".strip()

                ok = False
                for attempt in range(1, config.MAX_ATTEMPTS_PER_PRODUCT + 1):
                  try:
                    if self.is_blocked(page):
                        print(f"{search_text}: looks blocked, sleeping {config.BLOCK_BACKOFF_SECONDS}s")
                        time.sleep(config.BLOCK_BACKOFF_SECONDS)
                        raise RuntimeError("blocked")

                    product_pool = []
                    search_url = self.amazon_store_url + "s?k=" + "+".join(search_text.split(" "))
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
                        # Sponsored/video/brand-shelf cards can match role="listitem"
                        # while carrying a totally different internal structure - one
                        # such card used to raise AttributeError deep in here and
                        # abort the whole search, throwing away every other
                        # perfectly good candidate already collected. Skip just
                        # this one card instead.
                        try:
                            title_block = div.find('div', attrs={'data-cy': 'title-recipe'})
                            title_elem = title_block.find('a', recursive=False).find('span') if title_block else None
                            price_elem = div.find('div', attrs={'data-cy': 'price-recipe'})
                            price_elem = price_elem.find('span', class_ = 'a-offscreen') if price_elem else None
                            review_elem = div.find('div', attrs={'data-cy': 'reviews-block'})


                            if title_elem is None:
                                print(search_text + ": title cannot be found")
                                continue

                            if review_elem is None:
                                num_of_stars = 0.0
                                num_of_reviews = 0
                            else:
                                stars_elem = review_elem.find('span', class_ = ['a-size-small', 'a-color-base'])
                                count_elem = review_elem.find('span', class_ = ['a-size-mini', 'puis-normal-weight-text'])
                                if stars_elem is None or count_elem is None:
                                    num_of_stars = 0.0
                                    num_of_reviews = 0
                                else:
                                    num_of_stars = stars_elem.text
                                    num_of_reviews = count_elem.text

                                    num_of_reviews = str(num_of_reviews).strip("()").upper()
                                    if 'K' in num_of_reviews:
                                        num_of_reviews = int(float(num_of_reviews.replace('K','')) * 1000)
                                    elif 'M' in num_of_reviews:
                                        num_of_reviews = int(float(num_of_reviews.replace('M','')) * 1_000_000)
                                    else:
                                        num_of_reviews = int(num_of_reviews)



                            title = title_elem.text.strip()
                            clean_title = re.search(r'(.+?)(?:\s*[-,]\s*)',title).group(1).strip() if re.search(r'(.+?)(?:\s*[-,]\s*)',title) else title.strip()
                            price = float(re.search(r"\d[\d,]*(?:\.\d+)?", price_elem.text.strip()).group(0).replace(",", "")) if price_elem else None

                            num_of_ele = len(search_text.split()) + config.NUMBER_OF_EXTRA_WORDS
                            clean_title_v1 = " ".join((clean_title.split())[:num_of_ele])
                            clean_title_v2 = " ".join((title.split())[:num_of_ele])
                            score = max(fuzz.WRatio(search_text, clean_title_v1), fuzz.WRatio(search_text, clean_title_v2))
                            ASIN = div.get('data-asin')
                            if not ASIN:
                                continue
                            product_pool.append({
                                'title': title,
                                'clean_title_v1': clean_title_v1,
                                'clean_title_v2': clean_title_v2,
                                'ASIN': ASIN,
                                'price': price,
                                'num_of_stars': float(num_of_stars),
                                'num_of_reviews': num_of_reviews,
                                'score': score
                            })
                        except Exception as e:
                            print(f"{search_text}: skipping unparsable result card ({type(e).__name__}: {e})")
                            continue

                    if not product_pool:
                        print(search_text + ": price not found")
                        ok = True
                        break

                    exact_words = search_text.lower().split()[1:]

                    # Checked against the full listing title, not the
                    # clean_title_v1/v2 snippets - those are truncated to
                    # roughly the search term's own length purely to keep the
                    # fuzzy-match score fair, but colour is almost always the
                    # last word of a real Amazon title (after a long run of
                    # spec/marketing keywords), so truncating first would
                    # throw the colour away before this check ever saw it -
                    # silently rejecting real matches for every colour search.
                    # re.findall instead of .split() so trailing punctuation
                    # Amazon titles love (e.g. "... (Black)", "Mouse," ) doesn't
                    # keep an otherwise-exact word from matching.
                    filter_no_price_and_name_exists = [p for p in product_pool if p['price'] is not None and all(word in re.findall(r'[a-z0-9]+', p['title'].lower()) for word in exact_words)]
                    if not filter_no_price_and_name_exists:
                        print(search_text + ": price not found")
                        ok = True
                        break

                    # max_score (and thus score_diff) is taken from this
                    # already word/price-filtered set, not the raw
                    # product_pool - an unrelated same-brand product (e.g. a
                    # G305 result scoring as well as the searched-for G502)
                    # could otherwise set an artificially high ceiling that
                    # rejects every genuinely correct, priced candidate for
                    # having too large a score_diff from a product that was
                    # never actually a real match in the first place.
                    max_score = max(p['score'] for p in filter_no_price_and_name_exists)
                    for product in filter_no_price_and_name_exists:
                        product['score_diff'] = max_score - product['score']

                    candidates_for_price = [p for p in filter_no_price_and_name_exists if p['score_diff'] <= config.SIMILARITY_SCORE_DIFFERENCE_THRESHOLD  and all(word not in config.KEYWORDS_TO_EXCLUDE for word in re.findall(r'[a-z0-9]+', p['title'].lower()))]
                    if not candidates_for_price:
                        print(search_text + ": price not found")
                        ok = True
                        break

                    avg_reviews = sum(review['num_of_stars'] * review['num_of_reviews'] for review in candidates_for_price)/len(candidates_for_price)

                    for candidate in candidates_for_price:
                        candidate['weighted_review_score'] = (config.CONFIDENCE_LEVEL * avg_reviews + candidate['num_of_stars'] * candidate['num_of_reviews']) / (config.CONFIDENCE_LEVEL + candidate['num_of_reviews'])

                    

                    best_match_for_price = min(candidates_for_price, key = lambda x: x['price'])
                    best_match_for_reviews = max(candidates_for_price, key = lambda x: x['weighted_review_score'])

                    human_behaviour.human_mouse_move(page)
                    human_behaviour.human_pause(page, 2000, 5000)
                    data.append({
                        'skin_id': mouse['skin_id'],
                        'product_name': mouse['product_name'],
                        'colour': mouse['colour'],
                        'ASIN': best_match_for_price['ASIN'],
                        'link': f'https://www.amazon.sg/dp/{best_match_for_price["ASIN"]}',
                        'price': best_match_for_price['price'],
                        'num_of_stars': best_match_for_price['num_of_stars'],
                        'num_of_reviews': best_match_for_price['num_of_reviews'],
                        'sort_by': 'price'
                    })
                    data.append({
                        'skin_id': mouse['skin_id'],
                        'product_name': mouse['product_name'],
                        'colour': mouse['colour'],
                        'ASIN': best_match_for_reviews['ASIN'],
                        'link': f'https://www.amazon.sg/dp/{best_match_for_reviews["ASIN"]}',
                        'price': best_match_for_reviews['price'],
                        'num_of_stars': best_match_for_reviews['num_of_stars'],
                        'num_of_reviews': best_match_for_reviews['num_of_reviews'],
                        'sort_by': 'reviews'
                    })
                    ok = True
                    break
                  except Exception as e:
                    print(f"{search_text}: attempt {attempt} failed: {type(e).__name__}: {e}")

                if not ok:
                    failed.append(search_text)
                human_behaviour.polite_delay()

            page.close()
            browser.close()
            print(f'1st func: {failed}')
        return data
    
    def scrape_amazon_price_from_product_page(self, lst_of_mouse):
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
                ok = False
                for attempt in range(1, config.MAX_ATTEMPTS_PER_PRODUCT + 1):
                  extra = []
                  try:
                    if self.is_blocked(page):
                        print(f"{mouse['product_name']}: looks blocked, sleeping {config.BLOCK_BACKOFF_SECONDS}s")
                        time.sleep(config.BLOCK_BACKOFF_SECONDS)
                        raise RuntimeError("blocked")

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

                    data.append({
                        'skin_id': mouse['skin_id'],
                        'product_name': mouse['product_name'],
                        'date': datetime.date.today(),
                        'currency': currency,
                        'price': value,
                        'num_of_stars': mouse['num_of_stars'],
                        'num_of_reviews': mouse['num_of_reviews'],
                        'colour': mouse['colour'],
                        'store_link': mouse['link'],
                        'store_name': 'Amazon',
                        'sort_by': mouse['sort_by']
                    })
                # if other variant exists
                    if extra:
                        # Named distinctly from the outer loop's `mouse` -
                        # this used to reuse that name and shadow it, which
                        # was harmless before but would corrupt page.goto()
                        # on a retry attempt now that this block sits inside
                        # a retry loop keyed off the outer mouse.
                        for extra_mouse in extra:
                            page.goto(extra_mouse['link'])
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
                            review_elem = soup.find('div#averageCustomerReviews_feature_div')
                            num_of_stars = review_elem.find('span', class_ = ['a-size-small', 'a-color-base']).text
                            num_of_reviews = review_elem.find('span#acrCustomerReviewText').text

                            if num_of_reviews is None or num_of_stars is None:
                                num_of_stars = 0.0
                                num_of_reviews = 0
                            else:
                                num_of_stars = float(num_of_stars)
                                num_of_reviews = str(num_of_reviews).strip("()").upper()
                                if 'K' in num_of_reviews:
                                    num_of_reviews = int(float(num_of_reviews.replace('K','')) * 1000)
                                elif 'M' in num_of_reviews:
                                    num_of_reviews = int(float(num_of_reviews.replace('M','')) * 1_000_000)
                                else:
                                    num_of_reviews = int(num_of_reviews)

                            m_cur = re.match(r"^[^\d\s]+", price_with_currency)
                            currency = m_cur.group(0) if m_cur else None
                            m_num = re.search(r"\d[\d,]*(?:\.\d+)?", price_with_currency)
                            value = float(m_num.group(0).replace(",", "")) if m_num else None

                            colour = soup.find('table', class_ = 'a-normal')

                            if colour is None:
                                colour = None
                            else:
                                colour = colour.find('tr', class_ = 'po-color').find('span', class_ = 'po-break-word').text.strip()
                            data.append({
                                'product_name': extra_mouse['product_name'],
                                'date': datetime.date.today(),
                                'currency': currency,
                                'price': value,
                                'num_of_stars': num_of_stars,
                                'num_of_reviews': num_of_reviews,
                                'colour': colour,
                                'store_link': extra_mouse['link'],
                                'store_name': 'Amazon',
                                'sort_by': 'price'
                            })
                            human_behaviour.human_mouse_move(page)
                            human_behaviour.human_pause(page, 2000, 5000)

                    ok = True
                    break
                  except Exception as e:
                    print(f"{mouse['product_name']}: attempt {attempt} failed: {type(e).__name__}: {e}")

                if not ok:
                    failed.append(mouse)
                human_behaviour.polite_delay()

            page.close()
            browser.close()
            print(f'2nd func: {failed}')
        return data

    def run(self, lst_of_mouse):
        scraper = amazon_new_product_price_scraper()
        search_data = scraper.scrape_amazon_price(lst_of_mouse)
        price_data = scraper.scrape_amazon_price_from_product_page(search_data)
        return price_data

if __name__ == "__main__":
    scraper = amazon_new_product_price_scraper()
    lst_of_mouse = [
        {'skin_id': None, 'product_name': "Logitech G502 LIGHTSPEED", 'colour': "Black"},
        {'skin_id': None, 'product_name': "Logitech G502", 'colour': "Black"},
        {'skin_id': None, 'product_name': "Logitech G502 X", 'colour': "Black"},
    ]
    search_data = scraper.scrape_amazon_price(lst_of_mouse)
    print(search_data)
    price_data = scraper.scrape_amazon_price_from_product_page(search_data)
    print(price_data)




            

