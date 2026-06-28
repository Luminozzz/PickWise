"""Upscale scraped product image URLs to full resolution."""
import re
import urllib.parse


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
