import re
import random
# Keep the Chrome version in this UA reasonably close to the
# Chromium version Playwright ships

IDENTITY_PROFILES = [
    {
        "user_agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "viewport": {"width": 1366, "height": 768},
    },
    {
        "user_agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "viewport": {"width": 1920, "height": 1080},
    },
    {
        "user_agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "viewport": {"width": 1680, "height": 1050},
    },
]

_ACTIVE_PROFILE = random.choice(IDENTITY_PROFILES)

USER_AGENT = _ACTIVE_PROFILE["user_agent"]
VIEWPORT = _ACTIVE_PROFILE["viewport"]

# Spread into new_context() with ** unpacking — keys must match
# Playwright's parameter names exactly.
BROWSER_LAUNCH = {
    "user_data_dir": "./.playwright_profile",
    "headless": False,
    "args": ["--disable-blink-features=AutomationControlled"],
}

BROWSER_CONTEXT = {
    "user_agent": USER_AGENT,
    "viewport": VIEWPORT,
    "locale": "en-SG",
    "timezone_id": "Asia/Singapore",
    "geolocation": {"latitude": 1.3521, "longitude": 103.8198},
    "permissions": ["geolocation"],
    "extra_http_headers": {
        "Accept-Language": "en-SG,en;q=0.9",
    },
}

# Block heavy media to speed pages up.
BLOCK_RESOURCES = re.compile(
    r"\.(png|jpe?g|gif|webp|svg|avif|woff2?|ttf|mp4)(\?|$)",
    re.IGNORECASE,
)


# Playwright timeouts are in milliseconds.
PAGE_NAV_TIMEOUT = 60_000
DOM_WAIT_TIMEOUT = 100_000
SPEC_WAIT_TIMEOUT = 45_000
LOAD_MORE_TIMEOUT = 60_000

# How long _expand_specs keeps retrying (seconds)
EXPAND_SPECS_TOTAL_TIMEOUT = 45


MAX_ATTEMPTS_PER_PRODUCT = 2
BLOCK_BACKOFF_SECONDS = 900   # how long to sleep if we look blocked

# Title or Body fragments that suggest we've been blocked / challenged.
BLOCK_PAGE_MARKERS = ("the request could not be satisfied", "access denied", "are you a human", "just a moment",
               "pardon our interruption", "checking your browser",
               "verify you are human", "captcha")

# Comparing Number of products
NUMBER_OF_PRODUCTS_COMPARISON = 15

#Score difference threshold
SIMILARITY_SCORE_DIFFERENCE_THRESHOLD = 15
#Number of reviews such that we users would few comfortable to purchase the product
CONFIDENCE_LEVEL = 10

NUMBER_OF_EXTRA_WORDS = 2

KEYWORDS_TO_EXCLUDE = ['grip', 'case', 'casing','skates', 'glides', 'tape', 'supergrip', 'gears']