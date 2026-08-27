#!/usr/bin/env python3
"""Regenerate og.jpg — the link-preview countdown card — with today's days-left.

Runs daily via GitHub Actions just after midnight Kigali time, and can be run
locally from the repo root: python3 scripts/generate_og.py
Also bumps the ?v= cache-buster on the og:image tags in index.html.
"""
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from zoneinfo import ZoneInfo
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

W, H = 1200, 630
ESPRESSO = (36, 28, 22)
PANEL = (46, 36, 28)
IVORY = (243, 235, 221)
DIM = (217, 198, 168)
GOLD = (201, 169, 106)
TAUPE = (156, 139, 118)

KIGALI = ZoneInfo("Africa/Kigali")
TARGET = datetime(2026, 9, 5, 0, 0, tzinfo=KIGALI)
DAY_END = datetime(2026, 9, 6, 0, 0, tzinfo=KIGALI)

now = datetime.now(KIGALI)
remaining = (TARGET - now).total_seconds()
days = max(0, int(remaining // 86400))

italiana = lambda s: ImageFont.truetype(str(ASSETS / "Italiana-Regular.ttf"), s)
cormorant = lambda s: ImageFont.truetype(str(ASSETS / "CormorantGaramond-Medium.ttf"), s)
jost = lambda s: ImageFont.truetype(str(ASSETS / "Jost-Light.ttf"), s)

img = Image.new("RGB", (W, H), ESPRESSO)
d = ImageDraw.Draw(img)

# ——— right-side photo, cover-cropped ———
photo = Image.open(ASSETS / "card-photo.jpg")
pw, ph = 560, H
scale = max(pw / photo.width, ph / photo.height)
photo = photo.resize((round(photo.width * scale), round(photo.height * scale)))
left = (photo.width - pw) // 2
top = min(int(photo.height * 0.06), photo.height - ph)
photo = photo.crop((left, top, left + pw, top + ph))
img.paste(photo, (W - pw, 0))

# blend the photo into the espresso panel
grad = Image.new("L", (240, 1))
for x in range(240):
    grad.putpixel((x, 0), int(255 * (1 - x / 239)))
grad = grad.resize((240, H))
overlay = Image.new("RGB", (240, H), ESPRESSO)
img.paste(overlay, (W - pw, 0), grad)

# ——— hairline double frame ———
d.rectangle([16, 16, W - 17, H - 17], outline=GOLD + (0,), width=0)
d.rectangle([16, 16, W - 17, H - 17], outline=(151, 127, 80), width=2)
d.rectangle([26, 26, W - 27, H - 27], outline=(96, 81, 56), width=1)


def spaced(text, font, tracking):
    """Total width of text drawn with per-character tracking."""
    wsum = 0
    for ch in text:
        wsum += d.textlength(ch, font=font) + tracking
    return wsum - tracking


def draw_spaced(cx, y, text, font, tracking, fill):
    x = cx - spaced(text, font, tracking) / 2
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + tracking


def centered(cx, y, text, font, fill):
    d.text((cx - d.textlength(text, font=font) / 2, y), text, font=font, fill=fill)


CX = 340  # centre of the left panel

draw_spaced(CX, 52, "E · A", italiana(30), 10, GOLD)
draw_spaced(CX, 112, "THE WEDDING OF", jost(19), 9, TAUPE)
centered(CX, 148, "Eric & Antoinette", italiana(58), IVORY)

# ornament
d.line([CX - 130, 262, CX - 14, 262], fill=(120, 101, 67), width=1)
d.line([CX + 14, 262, CX + 130, 262], fill=(120, 101, 67), width=1)
dm = [(CX, 255), (CX + 7, 262), (CX, 269), (CX - 7, 262)]
d.polygon(dm, outline=GOLD)

if now >= DAY_END:
    centered(CX, 330, "Married", italiana(72), GOLD)
    centered(CX, 430, "September 5, 2026", cormorant(36), DIM)
elif now >= TARGET:
    centered(CX, 310, "Today, we say", italiana(56), GOLD)
    centered(CX, 385, "“I do.”", italiana(56), GOLD)
elif days == 0:
    centered(CX, 310, "Tomorrow,", italiana(56), GOLD)
    centered(CX, 385, "we say “I do.”", italiana(56), GOLD)
else:
    num = str(days)
    f = cormorant(215)
    box = d.textbbox((0, 0), num, font=f)
    d.text((CX - (box[2] - box[0]) / 2 - box[0], 268 - box[1]), num, font=f, fill=GOLD)
    label = "DAY TO GO" if days == 1 else "DAYS TO GO"
    draw_spaced(CX, 490, label, jost(22), 12, IVORY)

centered(CX, 545, "Saturday · September 5 · 2026", cormorant(30), DIM)

out = ROOT / "og.jpg"
img.save(out, quality=88, optimize=True)
print(f"og.jpg written — {days} day(s) to go as of {now:%Y-%m-%d %H:%M %Z}")

# bump the cache-buster in index.html so re-shared links fetch the fresh card
index = ROOT / "index.html"
html = index.read_text()
stamp = f"og.jpg?v={now:%Y%m%d}"
new = re.sub(r"og\.jpg(\?v=[0-9]+)?", stamp, html)
if new != html:
    index.write_text(new)
    print(f"index.html og:image bumped to {stamp}")
