import io
import os
import re
import socket
import ipaddress
from urllib.parse import urlparse, urljoin
from PIL import Image, ImageDraw, ImageFont
import requests
from bs4 import BeautifulSoup
import pytesseract
from pytesseract import Output
import cv2
import numpy as np
from dotenv import load_dotenv

load_dotenv()
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "").strip()
if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

def allowed_domains():
    return {x.strip().lower().rstrip(".") for x in os.getenv("ALLOWED_SOURCE_DOMAINS", "").split(",") if x.strip()}

def _public_host(host):
    if not host:
        return False
    try:
        infos = socket.getaddrinfo(host, None)
        for info in infos:
            ip = ipaddress.ip_address(info[4][0])
            if not ip.is_global:
                return False
        return bool(infos)
    except Exception:
        return False

def validate_url(url, domains=None):
    domains = allowed_domains() if domains is None else domains
    p = urlparse(url.strip())
    if p.scheme != "https" or not p.hostname:
        raise ValueError("Only HTTPS URLs are allowed.")
    host = p.hostname.lower().rstrip(".")
    if host not in domains:
        raise ValueError(f"Host '{host}' is not in ALLOWED_SOURCE_DOMAINS.")
    if not _public_host(host):
        raise ValueError("Host does not resolve to a public IP address.")
    return host

def safe_get(url, expected_host, timeout=20):
    validate_url(url, {expected_host})
    response = requests.get(url, timeout=timeout, allow_redirects=False, headers={"User-Agent":"LocalMangaTranslator/0.1"})
    if response.is_redirect:
        target = urljoin(url, response.headers.get("Location", ""))
        target_host = validate_url(target, {expected_host})
        if target_host != expected_host:
            raise ValueError("Redirect to a different host blocked.")
        response = requests.get(target, timeout=timeout, allow_redirects=False, headers={"User-Agent":"LocalMangaTranslator/0.1"})
    response.raise_for_status()
    return response

def fetch_page_images(page_url, max_images=100):
    host = validate_url(page_url)
    html = safe_get(page_url, host).text
    soup = BeautifulSoup(html, "html.parser")
    found, seen = [], set()
    for tag in soup.select("img"):
        src = tag.get("data-src") or tag.get("data-lazy-src") or tag.get("src")
        if not src:
            continue
        absolute = urljoin(page_url, src)
        try:
            image_host = validate_url(absolute)
        except ValueError:
            continue
        if image_host != host or absolute in seen:
            continue
        seen.add(absolute)
        found.append(absolute)
        if len(found) >= max_images:
            break
    return found

def download_images(urls, max_bytes=18_000_000):
    images = []
    for i, url in enumerate(urls, start=1):
        host = validate_url(url)
        r = safe_get(url, host, timeout=30)
        if len(r.content) > max_bytes:
            continue
        try:
            image = Image.open(io.BytesIO(r.content)).convert("RGB")
            if image.width < 100 or image.height < 100:
                continue
            images.append((f"page_{i:03d}.png", image))
        except Exception:
            continue
    return images

def image_to_png_bytes(image):
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()

def ocr_image(image):
    data = pytesseract.image_to_data(image, output_type=Output.DICT, config="--psm 11")
    items = []
    # Group neighboring words into a line, retaining a bounding box.
    groups = {}
    n = len(data.get("text", []))
    for i in range(n):
        word = (data["text"][i] or "").strip()
        try:
            conf = int(float(data["conf"][i]))
        except (ValueError, TypeError):
            conf = -1
        if not word or conf < 25:
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        x, y, w, h = (int(data[k][i]) for k in ("left", "top", "width", "height"))
        if key not in groups:
            groups[key] = {"text": word, "x": x, "y": y, "w": w, "h": h, "confidence": conf}
        else:
            g = groups[key]
            right, bottom = max(g["x"] + g["w"], x + w), max(g["y"] + g["h"], y + h)
            g["x"], g["y"] = min(g["x"], x), min(g["y"], y)
            g["w"], g["h"] = right - g["x"], bottom - g["y"]
            g["text"] += " " + word
            g["confidence"] = min(g["confidence"], conf)
    items = sorted(groups.values(), key=lambda z: (z["y"], z["x"]))
    return items

def translate_texts(texts, api_key, model="gemini-2.5-flash"):
    if not api_key:
        raise ValueError("Set GEMINI_API_KEY in .env to enable AI translation.")
    from google import genai
    client = genai.Client(api_key=api_key)
    results = []
    for text in texts:
        prompt = (
            "Translate the following manga/webtoon text into natural Myanmar (Burmese). "
            "Do not summarize or omit meaning. Preserve character names consistently; "
            "keep sound effects concise. Return only the Myanmar translation.\n\n"
            f"Source: {text}"
        )
        response = client.models.generate_content(model=model, contents=prompt)
        results.append((response.text or "").strip())
    return results

def clean_text_regions(image, items):
    # Conservative rectangular inpainting; inspect output because art may be damaged.
    arr = cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2BGR)
    mask = np.zeros(arr.shape[:2], dtype=np.uint8)
    for item in items:
        pad = max(2, int(min(item["w"], item["h"]) * 0.08))
        x1 = max(0, item["x"] - pad); y1 = max(0, item["y"] - pad)
        x2 = min(arr.shape[1], item["x"] + item["w"] + pad)
        y2 = min(arr.shape[0], item["y"] + item["h"] + pad)
        cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)
    cleaned = cv2.inpaint(arr, mask, 5, cv2.INPAINT_TELEA)
    return Image.fromarray(cv2.cvtColor(cleaned, cv2.COLOR_BGR2RGB))

def typeset_text(image, items, font_path=None):
    canvas = image.convert("RGB").copy()
    draw = ImageDraw.Draw(canvas)
    # Font needs Myanmar glyph support. Supply a Myanmar-capable TTF/OTF in settings.
    for item in items:
        text = (item.get("translated_text") or "").strip()
        if not text:
            continue
        x, y, w, h = item["x"], item["y"], item["w"], item["h"]
        font_size = max(12, min(36, int(h * 0.8)))
        font = None
        if font_path and os.path.isfile(font_path):
            try:
                font = ImageFont.truetype(font_path, font_size)
            except Exception:
                font = None
        if font is None:
            font = ImageFont.load_default()
        # White patch is intentionally conservative; complex bubbles need manual review.
        pad = max(2, int(h * 0.12))
        draw.rectangle((max(0,x-pad), max(0,y-pad), min(canvas.width,x+w+pad), min(canvas.height,y+h+pad)), fill="white")
        draw.multiline_text((x, y), text, fill="black", font=font, spacing=2, align="center")
    return canvas
