import math
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import random

def human_pause(page, min_ms=400, max_ms=1500):
    """Short 'thinking' pause. Use between discrete actions."""
    page.wait_for_timeout(random.randint(min_ms, max_ms))

def human_mouse_move(page, steps=None):
    """Move the mouse along a jittery path to a random point on screen."""
    width = page.viewport_size["width"]
    height = page.viewport_size["height"]
    target_x = random.randint(int(width * 0.2), int(width * 0.8))
    target_y = random.randint(int(height * 0.2), int(height * 0.8))
    # steps>1 makes Playwright interpolate intermediate points (a curve, not a teleport)
    page.mouse.move(target_x, target_y, steps=steps or random.randint(8, 25))

def human_scroll(page, total=None):
    """Scroll down in several small, uneven steps instead of one big jump."""
    total = total or random.randint(600, 1800)
    scrolled = 0
    while scrolled < total:
        step = random.randint(80, 250)
        page.mouse.wheel(0, step)
        scrolled += step
        page.wait_for_timeout(random.randint(150, 600))  # pause like a reader
    # occasionally scroll back up a little, like a human re-checking something
    if random.random() < 0.3:
        page.mouse.wheel(0, -random.randint(100, 400))
        human_pause(page, 300, 900)

def human_type(page, selector, text):
    """Type character-by-character with variable key delay (for search boxes)."""
    page.click(selector)
    human_pause(page, 200, 700)
    for char in text:
        page.keyboard.type(char, delay=random.randint(60, 220))
    human_pause(page, 300, 1000)

def human_hover(page, selector):
    """Hover over an element before acting on it (humans aim, then click)."""
    try:
        page.hover(selector, timeout=3000)
        human_pause(page, 200, 800)
    except PlaywrightTimeoutError:
        pass

def shuffled_subset(items, min_keep=None, max_keep=None):
    """Return the items in random order, optionally visiting only some of them.

    Mimics a human who doesn't check every product in a fixed sequence."""
    items = list(items)
    random.shuffle(items)
    if min_keep is None:
        return items 
    keep = random.randint(min_keep, min(max_keep or len(items), len(items)))
    return items[:keep]