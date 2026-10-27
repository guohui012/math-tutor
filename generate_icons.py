# -*- coding: utf-8 -*-
"""生成 PWA 图标（512 与 192）。运行一次即可：python generate_icons.py"""
import os

from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "icons")
os.makedirs(OUT, exist_ok=True)

BG = (15, 23, 42)       # 深蓝背景
ACCENT = (34, 211, 238)  # 青色符号

FONTS = [
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\seguisb.ttf",
]


def load_font(size):
    for fp in FONTS:
        try:
            return ImageFont.truetype(fp, size)
        except Exception:
            continue
    return None


def make(size, path):
    img = Image.new("RGB", (size, size), BG)
    d = ImageDraw.Draw(img)
    font = load_font(int(size * 0.55))
    text = "\u2211"  # ∑
    if font:
        bbox = d.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        d.text(((size - w) / 2 - bbox[0], (size - h) / 2 - bbox[1]), text, fill=ACCENT, font=font)
    else:
        d.text((size * 0.3, size * 0.3), text, fill=ACCENT)
    img.save(path)


make(512, os.path.join(OUT, "icon-512.png"))
make(192, os.path.join(OUT, "icon-192.png"))
print("icons generated in", OUT)
