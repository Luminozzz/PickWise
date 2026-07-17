
import os
import re
import random
# Keep the Chrome version in this UA reasonably close to the
# Chromium version Playwright ships

# Anchored to this file's directory so the profile path is stable
# regardless of the process's current working directory (e.g. when
# launched by Task Scheduler, which defaults cwd to System32).
_PROFILE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".playwright_profile")
# Acer gets its own profile dir so its Malaysia-locale identity (below) never
# mixes with the Singapore-locale history/cookies the shared profile has
# accumulated from the other scrapers.
_ACER_PROFILE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".playwright_profile_acer")

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
    "user_data_dir": _PROFILE_DIR,
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

# Acer-only: store.acer.com/en-sg is an SG storefront, but Akamai's bot
# detection flags the mismatch between claimed SG locale/timezone/geolocation
# and the machine's actual (Malaysia) network origin. This identity matches
# the real network origin instead. Other scrapers keep BROWSER_CONTEXT as-is.
ACER_BROWSER_LAUNCH = {
    **BROWSER_LAUNCH,
    "user_data_dir": _ACER_PROFILE_DIR,
}

ACER_BROWSER_CONTEXT = {
    **BROWSER_CONTEXT,
    "locale": "en-MY",
    "timezone_id": "Asia/Kuala_Lumpur",
    "geolocation": {"latitude": 3.1390, "longitude": 101.6869},
    "extra_http_headers": {
        "Accept-Language": "en-MY,en;q=0.9",
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

KEYWORDS_TO_EXCLUDE = ['set', 'combo', 'grip', 'case', 'casing','skates', 'glides', 'tape', 'supergrip', 'gears']


# =======================
# FORMAT
# =======================

# FORMAT_FORM_FACTOR = []
# FORMAT_PROGRAMMABLE_BUTTONS = []
# FORMAT_CONNECTIVITY = []
# FORMAT_BATTERY_LIFE = []
# FORMAT_MAX_DPI = []
# FORMAT_TRACKING_SPEED = []
# FORMAT_MAX_ACCELERATION = []
# FORMAT_WEIGHT = []
# FORMAT_SIZE = []
# FORMAT_POLLING_RATE = []
# FORMAT_RGB = []

# =======================
# RAZER
# =======================

RAZER_STORE_URL = "https://www.razer.com/sg-en/store/gaming-mice"
# Card titles containing any of these are bundles/add-ons, not standalone mice
# (e.g. "Razer Cobra Pro + Mouse Dock Pro Bundle").
RAZER_STORE_EXCLUDE_KEYWORDS = ['bundle', 'dock', 'puck', 'dongle', 'charging']

RAZER_FORM_FACTOR = ['form factor']
RAZER_PROGRAMMABLE_BUTTONS = ['programmable buttons']
RAZER_CONNECTIVITY = ['connectivity']
RAZER_BATTERY_LIFE = ['battery life']
RAZER_MAX_DPI = ["max sensitivity (dpi)"]
RAZER_TRACKING_SPEED = ["max speed (ips)"]
RAZER_MAX_ACCELERATION = ["max acceleration (g)"]
RAZER_WEIGHT = ["weight"]
RAZER_SIZE = ["size"]
RAZER_POLLING_RATE = ["polling rate / interval"]
RAZER_RGB = ['rgb lighting']

# =======================
# HP
# =======================
# HP's #specs panel is a nested {group: {label: value}} dict (see
# hp_scraper._extract_specs), not a flat spec-row list like Razer/Logitech -
# labels below are matched by exact equality against the (lowercased) label,
# same convention as RAZER_*.

HP_STORE_URL = "https://www.hp.com/sg-en/shop/accessories/mice.html"

HP_FORM_FACTOR = ['size & fit']
HP_PROGRAMMABLE_BUTTONS = ['buttons']
HP_CONNECTIVITY = ['connectivity', 'connection type']
HP_BATTERY_LIFE = ['battery life']
HP_MAX_DPI = ['resolution']
# Deliberately excludes "weight note (metric)" (e.g. HyperX's "with cable"
# figure) - only the plain "Weight" label is the mouse's own weight.
HP_WEIGHT = ['weight']
HP_SIZE = ['dimensions without stand (w x d x h)']

# Known errors on HP's own product pages that no generic parsing rule can
# tell apart from genuine data - keyed by exact product name, applied after
# cleaning to override just the listed fields.
HP_MANUAL_OVERRIDES = {
    "HP 240 Black Bluetooth Mouse": {
        # HP's page lists both "Connectivity: Wireless - USB Dongle" and
        # "Connection type: Bluetooth® 5.1" for this SKU, but every other
        # 240-series variant (Pike Silver, Empire Red, Lunar White) only
        # ever reports Bluetooth - the dongle line here is HP's own
        # copy-paste error, not a real second connectivity mode.
        'dongle': False,
    },
}

# =======================
# LOGITECH - NORMAL
# =======================

TITLE_WANTED = ['dimensions', 'technical specifications']

LOGITECH_FORM_FACTOR = ['hand_fit']
LOGITECH_PROGRAMMABLE_BUTTONS = ['number of buttons', 'programmable controls', 'button']
LOGITECH_CONNECTIVITY = ['connection type', 'wireless', 'required']
LOGITECH_BATTERY_LIFE = ['battery life', 'constant motion', 'battery']
LOGITECH_MAX_DPI = ['minimal and maximal value', 'dpi (minimal and maximal value)', 'sensor resolution', 'nominal value', 'resolution - tracking', 'max value', 'dpi (min/max)', 'dpi', 'resolution']
LOGITECH_TRACKING_SPEED = ['max. speed']
LOGITECH_MAX_ACCELERATION = ['max. acceleration']
LOGITECH_WEIGHT = ['weight']
LOGITECH_LENGTH = ['height']
LOGITECH_WIDTH = ['width']
LOGITECH_HEIGHT = ['depth']
LOGITECH_POLLING_RATE = ['max report rate', 'wireless report rate', 'usb report rate']
LOGITECH_RGB = ['rgb']

# =======================
# LOGITECH - GAMING
# =======================

TITLE_WANTED = ['dimensions', 'technical specifications']

LOGITECH_GAMING_FORM_FACTOR = ['hand_fit']
LOGITECH_GAMING_PROGRAMMABLE_BUTTONS = ['number of buttons', 'programmable controls', 'button']
LOGITECH_GAMING_CONNECTIVITY = ['connection type', 'wireless', 'required', 'name_desc']
LOGITECH_GAMING_BATTERY_LIFE = ['battery life', 'constant motion', 'battery']
LOGITECH_GAMING_MAX_DPI = ['minimal and maximal value', 'dpi (minimal and maximal value)', 'sensor resolution', 'nominal value', 'resolution - tracking', 'max value', 'dpi (min/max)', 'dpi', 'resolution']
LOGITECH_GAMING_TRACKING_SPEED = ['max. speed']
LOGITECH_GAMING_MAX_ACCELERATION = ['max. acceleration']
LOGITECH_GAMING_WEIGHT = ['weight']
LOGITECH_GAMING_LENGTH = ['depth', 'length']
LOGITECH_GAMING_WIDTH = ['width']
LOGITECH_GAMING_HEIGHT = ['height']
LOGITECH_GAMING_POLLING_RATE = ['max report rate', 'wireless report rate', 'usb report rate']
LOGITECH_GAMING_RGB = ['rgb']

# =======================
# ASUS
# =======================
# ASUS/ROG product pages expose a full spec table on a separate route from
# the overview page - /spec/ under rog.asus.com, /techspec/ under
# www.asus.com - keyed by the same kind of exact-label lookup Razer uses
# (labels are consistent ASUS copy, not freeform prose like Logitech's).

ASUS_FORM_FACTOR = ['shape']
ASUS_PROGRAMMABLE_BUTTONS = ['button']
ASUS_CONNECTIVITY = ['connectivity']
ASUS_BATTERY_LIFE = ['battery life']
ASUS_MAX_DPI = ['resolution']
ASUS_TRACKING_SPEED = ['max speed']
ASUS_MAX_ACCELERATION = ['max acceleration']
ASUS_WEIGHT = ['weight']
ASUS_SIZE = ['dimensions']
ASUS_POLLING_RATE = ['report rate']
ASUS_RGB = ['aura sync']
# "Color" is handled separately via the colour-swatch image carousel, and
# "Model" just repeats the product name - neither belongs in other_features.
ASUS_SKIP_FIELDS = ['color', 'model']

# ---- Existing spec patterns ----
PATTERNS = {
    "left_fit": None,
    "ergonomy": None,
    "max_DPI": re.compile(r"(\d[\d,]*\s*k?)\s*-?\s*dpi", re.I),
    "weight": re.compile(r"(\d+(?:\.\d+)?)\s*-?\s*gram", re.I),
    "programmable_buttons": re.compile(
        r"(\d+|\w+)"
        r"\s*programmable\s*buttons?", re.I),
    "battery_life": {
        "month": re.compile(r'(\d+)\s*months?', re.I),
        "day":   re.compile(r'(\d+)\s*days?', re.I),
        "hour":  re.compile(r'(\d+)\s*\+?\s*(?:hours?|hrs?|h)\b', re.I),
    },
    "polling_rate": re.compile(r"(\d[\d,]*)\s*hz", re.I),
    "wired": r"\bwired\b",
    "bluetooth": r"bluetooth",
    "dongle": [r"2\.4\s*ghz", r"\busb\b"],
    'acceleration': re.compile(r'(\d+)\s*ips\b', re.I),
    'tracking_speed': re.compile(r'(\d+)\s*g\b', re.I),
    'rgb': r"rgb",
}

SPECS_WO_COMPILE = ["left_fit", "ergonomy", "wired", "bluetooth", "dongle", "rgb"]
CONNECTIVITY = ["wired", "bluetooth", "dongle"]
SPECS_W_COMPILE = ["max_DPI", "weight", "programmable_buttons", "battery_life", "polling_rate", 'acceleration', "tracking_speed"]

CONNECTIVITY_TERMS = {
    "wired": r"\bwired\b",
    "wireless": r"\bwireless\b",
    "bluetooth": r"bluetooth",
    "2.4GHz": r"2\.4\s*ghz",
    "tri-mode": r"tri-mode",
    "dual-mode": r"dual-mode",
    "USB": r"\busb\b",
}

SHAPE_TERMS = {
    "ergonomic": r"ergonomic",
    "ambidextrous": r"ambidextrous",
    "symmetrical": r"symmetrical"
}

#---- Output dictionary ----

OUTPUT_DICT = {
    'product_name': None,
    'brand_name': None,
    'img_link': None,
    "alt_image": None,
    'left_fit': None,
    'ergonomy': None,
    'max_DPI': None,
    'weight': None,
    'length': None,
    'width': None,
    'number_of_buttons': None,
    'battery_life': None, # (min, max)
    'max_polling_rate': None,
    'other_features': None,
    'acceleration': None,
    'tracking_speed': None,
    'rgb': None,
    'bluetooth': None,
    'dongle': None,
    'wired': None
}

# ---- AMAZON product keys ----
AMAZON_CONNECTIVITY_TECHNOLOGY = "connectivity technology"
AMAZON_BUTTON_QUANTITY = "button quantity"
AMAZON_HAND_ORIENTATION = "hand orientation"
AMAZON_BATTERY_AVERAGE_LIFE = "battery average life"
AMAZON_MOUSE_MAXIMUM_SENSITIVITY = "mouse maximum sensitivity"
AMAZON_ITEM_WEIGHT = "item weight"
AMAZON_POWER_SOURCE = "power source"
AMAZON_ITEM_DIMENSIONS_L_X_W = "item dimensions l x w"

# if the mouse is wired, power source is corded electric
# if the mouse uses usb receiver, it has battery in it

POUNDS_TO_GRAMS = 453.592
CENTIMETRES_TO_MILLIMETRES = 10

# ---- SHOPEE OFFICIAL STORE CODE ----
