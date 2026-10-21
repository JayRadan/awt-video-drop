#!/usr/bin/env python3
"""Anonymous Wolf Trader brand kit: profile picture (800x800), channel banner (2560x1440 with safe area),
watermark (150x150), and a flat emblem. Original geometric wolf mark, gold on dark."""
import math, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

GOLD = (242, 193, 78); GOLD2 = (255, 224, 140); GOLD_D = (171, 134, 36)
BG = (7, 10, 16); PANEL = (11, 15, 24); GRID = (22, 29, 44); WHITE = (236, 240, 248); MUTED = (120, 132, 156); RED = (255, 77, 77); GREEN = (46, 230, 166)
FD = "/usr/share/fonts/opentype/inter/"
def font(sz, w="Bold", d=True):
    return ImageFont.truetype(FD + ("InterDisplay-" if d else "Inter-") + w + ".otf", sz)

WOLF = [(-0.95, -0.9), (-0.55, -0.25), (-0.75, 0.15), (-0.35, 0.55), (0, 0.95), (0.35, 0.55), (0.75, 0.15), (0.55, -0.25), (0.95, -0.9), (0.45, -0.55), (0, -0.4), (-0.45, -0.55)]

def wolf(d, g, cx, cy, s, col=GOLD, lw=None, fill=None):
    lw = lw or max(2, int(s / 12))
    poly = [(cx + x * s, cy + y * s) for x, y in WOLF]
    if fill: d.polygon(poly, fill=fill)
    d.line(poly + [poly[0]], fill=col, width=lw, joint="curve")
    g.line(poly + [poly[0]], fill=tuple(int(c * 0.6) for c in col), width=lw * 3)
    for ex in (-0.33, 0.33):
        e = [(cx + (ex - 0.14) * s, cy - 0.05 * s), (cx + ex * s, cy - 0.2 * s), (cx + (ex + 0.14) * s, cy - 0.05 * s)]
        d.line(e, fill=col, width=max(2, int(lw * 0.8)))
        g.line(e, fill=tuple(int(c * 0.8) for c in col), width=lw * 3)
    d.polygon([(cx - 0.1 * s, cy + 0.55 * s), (cx + 0.1 * s, cy + 0.55 * s), (cx, cy + 0.72 * s)], fill=col)

def composite(base, glow, k):
    b = np.asarray(base).astype(np.float32); gl = np.asarray(glow).astype(np.float32)
    gl = cv2.GaussianBlur(gl, (k, k), 0)
    return Image.fromarray(np.clip(b + gl, 0, 255).astype(np.uint8))

def radial_bg(w, h, cx=None, cy=None, inner=(16, 20, 32), outer=BG, r=None):
    cx = w / 2 if cx is None else cx; cy = h / 2 if cy is None else cy; r = r or max(w, h) * 0.7
    yy, xx = np.mgrid[0:h, 0:w]
    dd = np.clip(np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r, 0, 1)[..., None]
    arr = np.array(inner) * (1 - dd) + np.array(outer) * dd
    return Image.fromarray(arr.astype(np.uint8))

def grid(d, w, h, step, col=GRID):
    for x in range(0, w, step): d.line([(x, 0), (x, h)], fill=col, width=1)
    for y in range(0, h, step): d.line([(0, y), (w, y)], fill=col, width=1)

def candles_strip(d, g, x0, y0, w, h, n=40, seed=5):
    import random; random.seed(seed)
    p = 0.5; cw = w / n
    for i in range(n):
        o = p; c = max(0.08, min(0.92, o + random.gauss(0, 0.07))); hi = max(o, c) + abs(random.gauss(0, 0.04)); lo = min(o, c) - abs(random.gauss(0, 0.04))
        col = GREEN if c >= o else RED
        x = x0 + i * cw + cw / 2
        d.line([(x, y0 + h * (1 - hi)), (x, y0 + h * (1 - lo))], fill=tuple(int(v * 0.6) for v in col), width=max(1, int(cw * 0.12)))
        d.rectangle([x - cw * 0.3, y0 + h * (1 - max(o, c)), x + cw * 0.3, y0 + h * (1 - min(o, c)) + 1], fill=col)
        p = c

# ---------- profile picture ----------
def profile(size=800):
    img = radial_bg(size, size, inner=(20, 24, 38)); d = ImageDraw.Draw(img); grid(d, size, size, size // 12, (16, 21, 32))
    glow = Image.new("RGB", (size, size), (0, 0, 0)); g = ImageDraw.Draw(glow)
    # outer ring
    m = size * 0.06
    d.ellipse([m, m, size - m, size - m], outline=GOLD_D, width=int(size * 0.012))
    g.ellipse([m, m, size - m, size - m], outline=(90, 70, 20), width=int(size * 0.03))
    wolf(d, g, size / 2, size * 0.47, size * 0.30, GOLD, lw=int(size * 0.028))
    # small ticks at ring bottom like a dial
    for k in range(-5, 6):
        a = math.radians(90 + k * 7); r1 = size / 2 - m - size * 0.02; r2 = r1 - size * 0.025
        d.line([(size / 2 + r1 * math.cos(a), size / 2 + r1 * math.sin(a)), (size / 2 + r2 * math.cos(a), size / 2 + r2 * math.sin(a))], fill=GOLD_D if k else GOLD, width=3)
    f = font(int(size * 0.05), "ExtraBold"); txt = "AWT"
    d.text((size / 2 - d.textlength(txt, font=f) / 2, size * 0.78), txt, font=f, fill=WHITE)
    out = composite(img, glow, 61)
    return out

# ---------- banner ----------
def banner():
    W, H = 2560, 1440
    img = radial_bg(W, H, cx=W * 0.5, cy=H * 0.5, inner=(18, 22, 35), r=1500); d = ImageDraw.Draw(img); grid(d, W, H, 80, (14, 18, 28))
    glow = Image.new("RGB", (W, H), (0, 0, 0)); g = ImageDraw.Draw(glow)
    # faint candles across full width (visible on desktop, decorative)
    candles_strip(d, g, 0, H * 0.25, W, H * 0.5, n=96, seed=9)
    dark = Image.new("RGB", (W, H), BG); img = Image.blend(img, dark, 0.55); d = ImageDraw.Draw(img)
    # safe area 1546x423 centered
    sx0, sy0 = (W - 1546) / 2, (H - 423) / 2
    # emblem left of text within safe area
    wolf(d, g, sx0 + 170, H / 2 - 10, 140, GOLD, lw=14)
    # legibility plate behind the safe area text
    plate = Image.new("RGBA", (W, H), (0, 0, 0, 0)); pd = ImageDraw.Draw(plate)
    pd.rounded_rectangle([sx0 + 300, sy0 + 20, sx0 + 1546 - 10, sy0 + 423 - 20], radius=22, fill=(7, 10, 16, 215))
    img = Image.alpha_composite(img.convert("RGBA"), plate).convert("RGB"); d = ImageDraw.Draw(img)
    f1 = font(84, "ExtraBold"); f2 = font(34, "SemiBold", False); f3 = font(26, "Medium", False)
    tx = sx0 + 340
    d.text((tx, sy0 + 48), "ANONYMOUS", font=f1, fill=WHITE)
    d.text((tx + d.textlength("ANONYMOUS ", font=f1), sy0 + 48), "WOLF TRADER", font=f1, fill=GOLD)
    g.text((tx + d.textlength("ANONYMOUS ", font=f1), sy0 + 48), "WOLF TRADER", font=f1, fill=(70, 55, 15))
    d.rectangle([tx + 2, sy0 + 150, tx + 2 + 360, sy0 + 155], fill=GOLD)
    d.text((tx + 2, sy0 + 172), "Gold analysis from the order flow", font=f2, fill=WHITE)
    d.text((tx + 2, sy0 + 226), "NEW UPDATES 3× A WEEK  ·  XAUUSD  ·  NOT FINANCIAL ADVICE", font=f3, fill=MUTED)
    # pills
    x = tx + 2; y = sy0 + 280
    for tg in ["POSITIONING", "OPTION GAMMA", "MACRO REGIME"]:
        w_ = d.textlength(tg, font=f3) + 44
        d.rounded_rectangle([x, y, x + w_, y + 44], radius=22, fill=PANEL, outline=GOLD_D, width=2)
        d.text((x + 22, y + 8), tg, font=f3, fill=GOLD); x += w_ + 14
    out = composite(img, glow, 81)
    return out

def watermark(size=150):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    glow = Image.new("RGB", (size, size), (0, 0, 0)); g = ImageDraw.Draw(glow)
    wolf(d, g, size / 2, size * 0.5, size * 0.42, GOLD, lw=10)
    return img

def emblem(size=1024):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    glow = Image.new("RGB", (size, size), (0, 0, 0)); g = ImageDraw.Draw(glow)
    wolf(d, g, size / 2, size * 0.5, size * 0.42, GOLD, lw=int(size * 0.045))
    return img

if __name__ == "__main__":
    profile().save("AWT_profile_800.png")
    banner().save("AWT_banner_2560x1440.png")
    watermark().save("AWT_watermark_150.png")
    emblem().save("AWT_emblem_1024.png")
    # banner previews: desktop/tv (full), tablet (1855x423 center), mobile (1546x423)
    b = Image.open("AWT_banner_2560x1440.png")
    W, H = b.size
    b.crop(((W - 1546) // 2, (H - 423) // 2, (W + 1546) // 2, (H + 423) // 2)).save("preview_banner_mobile.png")
    print("done")
