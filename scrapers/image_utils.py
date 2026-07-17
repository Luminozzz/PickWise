"""Upscale scraped product image URLs to full resolution."""
import json
import re
import urllib.parse
import urllib.request


def razer_full_res(url):
    """Razer's assets3.razerzone.com URLs embed the original (full-res) image,
    URL-encoded, after the /<W>x<H>/ resize token. Return that original; pass
    non-Razer / unrecognised URLs through unchanged."""
    if not url or "razerzone.com" not in url:
        return url
    parts = re.split(r"/\d+x\d+/", url, maxsplit=1)
    if len(parts) == 2 and parts[1]:
        return urllib.parse.unquote(parts[1])
    return url


def logitech_hi_res(url):
    """Bump Logitech's Cloudinary-style transform (w_416,h_312,...) to a larger
    size. The transform is unsigned, so this just yields a higher-res render."""
    if not url or "resource.logitech.com" not in url:
        return url
    url = re.sub(r"w_\d+", "w_900", url, count=1)
    url = re.sub(r"h_\d+", "h_675", url, count=1)
    return url


def ugreen_hi_res(url):
    """UGreen's Shopify CDN serves gallery images as
    //www.ugreen.com/cdn/shop/files/<name>.<ext>?v=<version>&width=<px>.
    Dropping the width param yields the original full-resolution file (the
    largest entry in the tag's own srcset); also normalises the
    protocol-relative URL to https so it's usable outside a browser."""
    if not url:
        return url
    if url.startswith("//"):
        url = "https:" + url
    parts = urllib.parse.urlsplit(url)
    query = [(k, v) for k, v in urllib.parse.parse_qsl(parts.query) if k != "width"]
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, urllib.parse.urlencode(query), parts.fragment))


def hp_dedupe_gallery(url):
    """HP's CDN (sg-media.apjonlinecdn.com) serves the same image under both
    its original path and a resized /catalog/product/cache/<hash>/ path.
    Strip the cache segment so both variants collapse to one canonical URL."""
    if not url:
        return url
    return re.sub(r"/cache/[a-f0-9]+/", "/", url)


def razer_primary_render(product_url, timeout=30):
    """Fetch a Razer product page and return its PRIMARY transparent product
    render (decoded to full resolution) from the page's JSON-LD. Useful for
    products with no colour variants on the store page. None on any failure."""
    if not product_url or "razer.com" not in product_url:
        return None
    page = re.sub(r"/buy/?$", "", product_url)
    try:
        req = urllib.request.Request(page, headers={"User-Agent": "Mozilla/5.0"})
        html = urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "ignore")
    except Exception:
        return None
    for block in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', html, re.S):
        try:
            data = json.loads(block)
        except Exception:
            continue
        for obj in (data if isinstance(data, list) else [data]):
            if isinstance(obj, dict) and obj.get("image"):
                img = obj["image"]
                img = img[0] if isinstance(img, list) else img
                return razer_full_res(img)
    return None
