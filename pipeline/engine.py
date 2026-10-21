#!/usr/bin/env python3
"""Anonymous Wolf Trader — quant-terminal video engine.
Usage: python3 engine.py timing.json out.mp4 [start_sec end_sec]
Renders 1920x1080 @30fps, video only (audio muxed separately).
"""
import sys, json, math, random
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1920, 1080, 30
T = json.load(open(sys.argv[1]))
OUT = sys.argv[2]
T0 = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
T1 = float(sys.argv[4]) if len(sys.argv) > 4 else T["scenes"][-1]["end"] + 2.5
TOTAL = T["scenes"][-1]["end"] + 2.5

# ---------- palette ----------
BG = (7, 10, 16); PANEL = (11, 15, 24); PANEL2 = (15, 20, 31); GRID = (22, 29, 44); GRID2 = (32, 41, 60)
GOLD = (242, 193, 78); GOLD2 = (255, 224, 140); RED = (255, 77, 77); GREEN = (46, 230, 166); CYAN = (55, 200, 255)
WHITE = (236, 240, 248); MUTED = (120, 132, 156); DIM = (70, 80, 100)

FD = "/usr/share/fonts/opentype/inter/"
def font(sz, w="Bold", d=True):
    return ImageFont.truetype(FD + ("InterDisplay-" if d else "Inter-") + w + ".otf", sz)
F = {k: font(*v) for k, v in {
    "hero": (120, "ExtraBold"), "h1": (74, "ExtraBold"), "h2": (48, "Bold"), "h3": (34, "SemiBold"),
    "body": (30, "Medium", False), "cap": (40, "SemiBold", False), "sm": (22, "Medium", False),
    "tag": (20, "SemiBold", False), "mono": (24, "Medium", False), "num": (150, "ExtraBold"),
    "tiny": (17, "Medium", False)}.items()}

def ease(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3
def ease_io(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
def mix(a, b, u): return tuple(int(a[i] + (b[i] - a[i]) * u) for i in range(3))
def alpha(c, u): return mix(BG, c, u)

# ---------- synthetic market structure (illustrative) ----------
random.seed(11)
LEVEL = 4150.0
def gen_candles(n=170):
    out, p = [], 4118.0
    for i in range(n):
        drift = 0.0
        o = p
        # hourly-ish random walk inside a range, capped under the level
        c = o + random.gauss(drift, 6.5)
        if i > n - 34:           # last stretch: pushes up into 4150 and rejects
            c = o + random.gauss(1.2, 5.5)
        c = min(c, LEVEL - 2 - random.random() * 6)
        c = max(c, 4086 + random.random() * 6)
        hi = max(o, c) + abs(random.gauss(0, 4))
        lo = min(o, c) - abs(random.gauss(0, 4))
        if i > n - 30 and random.random() < 0.45:
            hi = LEVEL + random.random() * 3.5     # wick pokes at the level and fails
        hi = min(hi, LEVEL + 4)
        vol = abs(c - o) * 40 + random.random() * 120 + (160 if i > n - 30 else 0)
        out.append((o, hi, lo, c, vol)); p = c
    return out
C = gen_candles()
N = len(C)
PMIN, PMAX = 4072.0, 4186.0

# gamma profile by strike (illustrative): puts negative, calls positive
STRIKES = list(range(4050, 4255, 10))
def gamma_profile():
    prof = {}
    for s in STRIKES:
        put = 0.15 + 0.5 * math.exp(-((s - 4100) / 40) ** 2) + random.random() * 0.1
        call = 0.1 + 0.45 * math.exp(-((s - 4200) / 45) ** 2) + random.random() * 0.1
        if s == 4150: put = 1.0; call = 0.12
        if s == 4140: put = 0.62
        if s == 4160: put = 0.58
        prof[s] = (put, call)
    return prof
GP = gamma_profile()

# ---------- helpers ----------
def new_layers():
    base = Image.new("RGB", (W, H), BG)
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    return base, ImageDraw.Draw(base), glow, ImageDraw.Draw(glow)

def composite(base, glow, strength=1.0, k=41):
    b = np.asarray(base).astype(np.float32)
    g = np.asarray(glow).astype(np.float32)
    g = cv2.GaussianBlur(g, (k, k), 0) * strength
    out = np.clip(b + g, 0, 255).astype(np.uint8)
    return out

_bg_cache = None
def background():
    global _bg_cache
    if _bg_cache is not None: return _bg_cache.copy()
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)
    # perspective floor grid
    hz = 700
    for i in range(-16, 17):
        x0 = W / 2 + i * 60; x1 = W / 2 + i * 420
        d.line([(x0, hz), (x1, H)], fill=(14, 19, 30), width=1)
    y = hz
    for k in range(14):
        y += 8 + k * 5
        if y > H: break
        d.line([(0, y), (W, y)], fill=(14, 19, 30), width=1)
    # fine grid
    for x in range(0, W, 64): d.line([(x, 0), (x, hz)], fill=(12, 16, 25), width=1)
    for yy in range(0, hz, 64): d.line([(0, yy), (W, yy)], fill=(12, 16, 25), width=1)
    arr = np.asarray(img).astype(np.float32)
    # vignette + top glow
    yy, xx = np.mgrid[0:H, 0:W]
    v = 1 - 0.55 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) ** 1.2
    arr *= np.clip(v, 0.3, 1)[..., None]
    _bg_cache = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    return _bg_cache.copy()

def rr(d, box, r, fill, outline=None, width=1):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)

def tw(d, text, f): return d.textlength(text, font=f)

def wolf_mark(d, g, cx, cy, s, col=GOLD, u=1.0):
    """Original geometric wolf emblem, line art. s = half-size."""
    pts = [(-0.95, -0.9), (-0.55, -0.25), (-0.75, 0.15), (-0.35, 0.55), (0, 0.95), (0.35, 0.55), (0.75, 0.15), (0.55, -0.25), (0.95, -0.9), (0.45, -0.55), (0, -0.4), (-0.45, -0.55)]
    poly = [(cx + x * s, cy + y * s) for x, y in pts]
    c = alpha(col, u)
    d.line(poly + [poly[0]], fill=c, width=max(2, int(s / 14)))
    g.line(poly + [poly[0]], fill=mix((0, 0, 0), col, 0.5 * u), width=max(4, int(s / 7)))
    # eyes
    for ex in (-0.33, 0.33):
        e = [(cx + (ex - 0.14) * s, cy - 0.05 * s), (cx + ex * s, cy - 0.2 * s), (cx + (ex + 0.14) * s, cy - 0.05 * s)]
        d.line(e, fill=c, width=max(2, int(s / 16)))
        g.line(e, fill=mix((0, 0, 0), col, 0.7 * u), width=max(4, int(s / 8)))
    # nose
    d.polygon([(cx - 0.1 * s, cy + 0.55 * s), (cx + 0.1 * s, cy + 0.55 * s), (cx, cy + 0.72 * s)], fill=c)

def topbar(d, g, t, u=1.0, price=None):
    rr(d, [0, 0, W, 84], 0, PANEL)
    d.line([(0, 84), (W, 84)], fill=GRID2, width=1)
    wolf_mark(d, g, 64, 42, 26, GOLD, u)
    d.text((110, 20), "ANONYMOUS WOLF TRADER", font=F["h3"], fill=alpha(WHITE, u))
    d.text((600, 30), "XAUUSD  ·  GOLD UPDATE  ·  21 OCT 2026", font=F["tag"], fill=alpha(MUTED, u))
    # live readout
    p = price if price is not None else C[-1][3]
    flick = p + math.sin(t * 7.3) * 0.6 + math.sin(t * 2.1) * 0.4
    s = f"{flick:,.2f}"
    d.text((W - 110 - tw(d, s, F["h3"]), 18), s, font=F["h3"], fill=alpha(GOLD, u))
    g.text((W - 110 - tw(d, s, F["h3"]), 18), s, font=F["h3"], fill=mix((0, 0, 0), GOLD, 0.35 * u))
    d.text((W - 395, 26), "GC FUT", font=F["tag"], fill=alpha(MUTED, u))
    dot = alpha(GREEN if int(t * 2) % 2 == 0 else (20, 90, 60), u)
    d.ellipse([W - 425, 36, W - 413, 48], fill=dot)
    d.text((W - 60, 26), "LIVE", font=F["tag"], fill=alpha(MUTED, u))

TICK = [("XAUUSD", "4,147.80", -0.42), ("XAGUSD", "51.92", -0.88), ("DXY", "103.84", +0.21), ("US10Y", "4.31%", +0.03),
        ("WTI", "61.40", -1.12), ("GC DEC26", "4,151.2", -0.39), ("SPX", "6,842", +0.18), ("BTC", "118,420", -0.6)]
def ticker(d, t, u=1.0):
    y = H - 46
    rr(d, [0, y - 12, W, H], 0, PANEL)
    d.line([(0, y - 12), (W, y - 12)], fill=GRID2, width=1)
    x = -int((t * 110) % 2600)
    while x < W:
        for sym, px, chg in TICK:
            col = GREEN if chg >= 0 else RED
            d.text((x, y), sym, font=F["tag"], fill=alpha(MUTED, u)); x += tw(d, sym, F["tag"]) + 14
            d.text((x, y), px, font=F["tag"], fill=alpha(WHITE, u)); x += tw(d, px, F["tag"]) + 10
            s = f"{chg:+.2f}%"; d.text((x, y), s, font=F["tag"], fill=alpha(col, u)); x += tw(d, s, F["tag"]) + 48

def caption(d, g, t, u=1.0):
    cur = next((s for s in T["sentences"] if s["start"] <= t < s["end"]), None)
    if not cur: return
    txt = cur["text"]
    lt = t - cur["start"]
    # wrap to lines of <= 1400px
    words = txt.split(); lines = []; line = ""
    for wd in words:
        trial = (line + " " + wd).strip()
        if tw(d, trial, F["cap"]) > 1400 and line:
            lines.append(line); line = wd
        else:
            line = trial
    if line: lines.append(line)
    n = int(min(len(txt), lt * 55))
    w = max(tw(d, l, F["cap"]) for l in lines)
    lh = 52; y = H - 110 - lh * len(lines)
    x = (W - w) / 2
    rr(d, [x - 28, y - 14, x + w + 28, y + lh * len(lines) + 8], 12, (9, 12, 20), outline=GRID2)
    d.rectangle([x - 28, y - 14, x - 22, y + lh * len(lines) + 8], fill=GOLD)
    consumed = 0
    for k, l in enumerate(lines):
        seg = l[:max(0, n - consumed)]
        d.text((x, y + k * lh), seg, font=F["cap"], fill=alpha(WHITE, u))
        consumed += len(l) + 1

# ---------- chart ----------
def chart(d, g, box, t, i0=0, i1=None, frac=1.0, level=False, level_u=1.0, playhead=True, zoom_u=0.0,
          rejections=False, breakdown=0.0, wall=False, title=None, crosshair=True):
    x0, y0, x1, y1 = box
    i1 = N if i1 is None else i1
    rr(d, box, 10, PANEL, outline=GRID2)
    for (cx_, cy_, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        d.line([(cx_ + sx * 4, cy_ + sy * 30), (cx_ + sx * 4, cy_ + sy * 4), (cx_ + sx * 30, cy_ + sy * 4)], fill=GOLD, width=2)
    # zoom: interpolate visible window
    a = int(i0 + (i0 - 0) * 0); b = i1
    lo_p, hi_p = PMIN, PMAX
    if zoom_u > 0:
        a = int(0 + (N - 46) * zoom_u); lo_p = PMIN + (4098 - PMIN) * zoom_u; hi_p = PMAX - (PMAX - 4170) * zoom_u
    vis = list(range(a, b))
    n_show = max(2, int(len(vis) * frac))
    vis = vis[:n_show]
    cw = (x1 - x0 - 150) / max(len(range(a, b)), 1)
    def px(i): return x0 + 24 + (i - a) * cw
    def py(p): return y1 - 70 - (p - lo_p) / (hi_p - lo_p) * (y1 - y0 - 110)
    # grid + axis
    step = 20 if (hi_p - lo_p) > 80 else 10
    p = math.ceil(lo_p / step) * step
    while p < hi_p:
        yy = py(p); d.line([(x0 + 12, yy), (x1 - 120, yy)], fill=GRID, width=1)
        d.text((x1 - 105, yy - 12), f"{p:,.0f}", font=F["sm"], fill=DIM); p += step
    if title:
        d.text((x0 + 24, y0 + 16), title, font=F["tag"], fill=MUTED)
    # volume
    vmax = max(c[4] for c in C)
    for i in vis:
        o, hi, lo, c, v = C[i]
        xx = px(i); hh = (v / vmax) * 70
        d.rectangle([xx - cw * 0.3, y1 - 12 - hh, xx + cw * 0.3, y1 - 12], fill=(20, 27, 40) if c >= o else (36, 22, 28))
    # candles
    for i in vis:
        o, hi, lo, c, v = C[i]
        xx = px(i); up = c >= o
        col = GREEN if up else RED
        d.line([(xx, py(hi)), (xx, py(lo))], fill=mix(BG, col, 0.75), width=2)
        d.rectangle([xx - cw * 0.34, py(max(o, c)), xx + cw * 0.34, py(min(o, c)) + 1], fill=col)
    # close line glow
    pts = [(px(i), py(C[i][3])) for i in vis]
    g.line(pts, fill=(60, 48, 16), width=6)
    # level
    if level:
        ly = py(LEVEL); xe = x0 + 12 + int((x1 - 120 - x0 - 12) * level_u)
        for xx in range(x0 + 12, xe, 28):
            d.line([(xx, ly), (min(xx + 16, xe), ly)], fill=RED, width=3)
        g.line([(x0 + 12, ly), (xe, ly)], fill=(70, 20, 20), width=8)
        if level_u >= 1:
            lab = "4,150  ·  DEALER GAMMA  ·  PUT WALL"
            lw = tw(d, lab, F["tag"])
            rr(d, [x0 + 24, ly - 46, x0 + 24 + lw + 30, ly - 10], 6, (50, 16, 20), outline=RED)
            d.text((x0 + 39, ly - 40), lab, font=F["tag"], fill=RED)
        if wall:
            # shaded zone above the level
            ov = Image.new("RGBA", (x1 - x0, int(ly) - y0), (255, 77, 77, 0))
            od = ImageDraw.Draw(ov)
            for k in range(int(ly) - y0 - 20, int(ly) - y0):
                od.line([(12, k), (x1 - x0 - 120, k)], fill=(255, 77, 77, int(60 * (k - (int(ly) - y0 - 20)) / 20)))
            # paste via numpy
            base = d._image
            base.paste(Image.alpha_composite(base.crop((x0, y0, x1, int(ly))).convert("RGBA"), ov).convert("RGB"), (x0, y0))
    if rejections:
        ly = py(LEVEL)
        hits = [i for i in vis if C[i][1] >= LEVEL - 0.5][-6:]
        for k, i in enumerate(hits):
            xx = px(i)
            d.ellipse([xx - 12, ly - 12, xx + 12, ly + 12], outline=RED, width=2)
            g.ellipse([xx - 14, ly - 14, xx + 14, ly + 14], outline=(120, 30, 30), width=4)
            d.line([(xx, ly + 14), (xx, ly + 50)], fill=RED, width=3)
            d.polygon([(xx - 8, ly + 44), (xx + 8, ly + 44), (xx, ly + 58)], fill=RED)
    if playhead and pts:
        lx, lyy = pts[-1]
        if crosshair:
            d.line([(lx, y0 + 12), (lx, y1 - 12)], fill=(40, 52, 78), width=1)
            d.line([(x0 + 12, lyy), (x1 - 120, lyy)], fill=(40, 52, 78), width=1)
        d.ellipse([lx - 7, lyy - 7, lx + 7, lyy + 7], fill=WHITE)
        g.ellipse([lx - 12, lyy - 12, lx + 12, lyy + 12], fill=(90, 80, 40))
        pr = f"{C[vis[-1]][3]:,.1f}"
        rr(d, [x1 - 118, lyy - 16, x1 - 10, lyy + 16], 5, GOLD)
        d.text((x1 - 112, lyy - 12), pr, font=F["sm"], fill=(20, 16, 6))
    if breakdown > 0 and pts:
        lx, lyy = pts[-1]
        ex = lx + 260 * breakdown; ey = lyy + 300 * breakdown
        d.line([(lx, lyy), (ex, ey)], fill=RED, width=8)
        g.line([(lx, lyy), (ex, ey)], fill=(110, 30, 30), width=18)
        ang = math.atan2(ey - lyy, ex - lx); ah = 34
        d.polygon([(ex, ey), (ex - ah * math.cos(ang - 0.45), ey - ah * math.sin(ang - 0.45)), (ex - ah * math.cos(ang + 0.45), ey - ah * math.sin(ang + 0.45))], fill=RED)
        if breakdown >= 1:
            d.text((ex + 20, ey - 10), "EXPECTED PATH", font=F["tag"], fill=RED)
    return px, py

def gamma_panel(d, g, box, t, u=1.0, highlight=False):
    x0, y0, x1, y1 = box
    rr(d, box, 10, PANEL, outline=GRID2)
    d.text((x0 + 20, y0 + 16), "OPTION GAMMA PROFILE · BY STRIKE", font=F["tag"], fill=alpha(MUTED, u))
    d.text((x0 + 20, y0 + 42), "puts", font=F["tiny"], fill=alpha(RED, u)); d.text((x1 - 60, y0 + 42), "calls", font=F["tiny"], fill=alpha(GREEN, u))
    mid = (x0 + x1) / 2 + 20
    rows = STRIKES[::-1]
    rh = (y1 - y0 - 90) / len(rows)
    for k, s in enumerate(rows):
        yy = y0 + 72 + k * rh
        put, call = GP[s]
        pw = put * (mid - x0 - 90) * u; cw_ = call * (x1 - mid - 30) * u
        pc = RED if not (highlight and s == 4150) else (255, 120, 120)
        d.rectangle([mid - pw, yy + 3, mid, yy + rh - 3], fill=mix(BG, pc, 0.85 if s == 4150 else 0.55))
        d.rectangle([mid, yy + 3, mid + cw_, yy + rh - 3], fill=mix(BG, GREEN, 0.5))
        if s == 4150:
            g.rectangle([mid - pw, yy, mid, yy + rh], fill=(110, 30, 30))
        d.text((x0 + 18, yy + rh / 2 - 9), f"{s:,}", font=F["tiny"], fill=alpha(GOLD if s == 4150 else DIM, u))
    d.line([(mid, y0 + 66), (mid, y1 - 14)], fill=GRID2, width=1)
    if highlight:
        d.text((x0 + 20, y1 - 40), "4,150 = heaviest put strike · dealers hedge here", font=F["tiny"], fill=alpha(GOLD, u))

def positioning_panel(d, g, box, t, u=1.0):
    x0, y0, x1, y1 = box
    rr(d, box, 10, PANEL, outline=GRID2)
    d.text((x0 + 20, y0 + 16), "POSITIONING · SHORT-SIDE FLOW", font=F["tag"], fill=alpha(MUTED, u))
    rows = [("SPECULATORS", 0.82), ("INSTITUTIONAL", 0.68), ("CHINA", 0.9)]
    for k, (name, v) in enumerate(rows):
        yy = y0 + 70 + k * 92
        uu = ease((u * 3) - k * 0.6)
        d.text((x0 + 20, yy), name, font=F["sm"], fill=alpha(WHITE, uu))
        d.text((x1 - 90, yy), "SHORT", font=F["tag"], fill=alpha(RED, uu))
        d.rectangle([x0 + 20, yy + 34, x1 - 20, yy + 48], fill=GRID)
        wv = int((x1 - x0 - 40) * v * uu)
        d.rectangle([x0 + 20, yy + 34, x0 + 20 + wv, yy + 48], fill=RED)
        g.rectangle([x0 + 20, yy + 34, x0 + 20 + wv, yy + 48], fill=(90, 25, 25))
    d.text((x0 + 20, y1 - 40), "entering the short side of gold", font=F["tiny"], fill=alpha(MUTED, u))

def macro_panel(d, g, box, t, u=1.0):
    x0, y0, x1, y1 = box
    rr(d, box, 10, PANEL, outline=GRID2)
    d.text((x0 + 20, y0 + 16), "MACRO REGIME", font=F["tag"], fill=alpha(MUTED, u))
    rows = [("FED EXPECTATIONS", "bearish gold"), ("THE DATA", "bearish gold"), ("OIL", "bearish gold"), ("YIELDS", "bearish gold")]
    for k, (a, b) in enumerate(rows):
        yy = y0 + 62 + k * 86
        uu = ease((u * 3) - k * 0.5)
        rr(d, [x0 + 16, yy, x1 - 16, yy + 72], 8, alpha(PANEL2, uu), outline=alpha(GRID2, uu))
        d.rectangle([x0 + 16, yy, x0 + 22, yy + 72], fill=alpha(RED, uu))
        d.text((x0 + 38, yy + 12), a, font=F["sm"], fill=alpha(WHITE, uu))
        d.text((x0 + 38, yy + 42), b, font=F["tiny"], fill=alpha(RED, uu))
        # sparkline
        random.seed(k + 3); sp = [random.random() for _ in range(18)]
        spts = [(x1 - 150 + j * 7, yy + 50 - sp[j] * 30 - j * 0.8) for j in range(18)]
        d.line(spts, fill=alpha(RED, uu), width=2)

def big_label(d, g, x, y, text, col, u, f="h1"):
    d.text((x, y), text, font=F[f], fill=alpha(col, u))
    g.text((x, y), text, font=F[f], fill=mix((0, 0, 0), col, 0.35 * u))

# ---------- scenes ----------
SC = {s["para"]: s for s in T["scenes"]}
def scene_at(t):
    for s in T["scenes"]:
        if s["start"] <= t < s["end"]: return s
    return T["scenes"][0] if t < T["scenes"][0]["start"] else T["scenes"][-1]

CHART_BOX = (40, 110, 1340, 870)
SIDE_BOX = (1370, 110, 1880, 870)

def render(t):
    base = background(); d = ImageDraw.Draw(base)
    glow = Image.new("RGB", (W, H), (0, 0, 0)); g = ImageDraw.Draw(glow)
    d._image = base
    s = scene_at(t); p = s["para"]; lt = t - s["start"]; u = ease(lt / 0.5)

    if p == 0:  # intro
        v = ease(t / 0.8)
        wolf_mark(d, g, W / 2, 330, 150 * (0.6 + 0.4 * v), GOLD, v)
        big_label(d, g, W / 2 - tw(d, "ANONYMOUS WOLF TRADER", F["h1"]) / 2, 520, "ANONYMOUS WOLF TRADER", WHITE, ease((t - 0.4) / 0.6))
        d.rectangle([W / 2 - 240 * ease((t - 0.9) / 0.6), 615, W / 2 + 240 * ease((t - 0.9) / 0.6), 619], fill=GOLD)
        sub = "GOLD UPDATE  ·  21 OCT 2026  ·  XAUUSD"
        d.text((W / 2 - tw(d, sub, F["h3"]) / 2, 640), sub, font=F["h3"], fill=alpha(MUTED, ease((t - 1.2) / 0.6)))
        tags = ["POSITIONING", "OPTION GAMMA", "MACRO REGIME"]
        xx = W / 2 - 420
        for k, tg in enumerate(tags):
            uu = ease((t - 1.8 - k * 0.25) / 0.5)
            rr(d, [xx, 720, xx + 260, 768], 24, alpha(PANEL2, uu), outline=alpha(GOLD, uu * 0.6))
            d.text((xx + 130 - tw(d, tg, F["tag"]) / 2, 734), tg, font=F["tag"], fill=alpha(GOLD, uu))
            xx += 290
        # scanning line
        sy = int((t * 260) % H)
        d.line([(0, sy), (W, sy)], fill=(20, 28, 44), width=2)
    elif p == 1:  # range
        topbar(d, g, t, u); ticker(d, t, u)
        chart(d, g, CHART_BOX, t, frac=ease(lt / 6.0), title="XAUUSD · 1H · LAST 2 WEEKS", level=False)
        x0, y0, x1, y1 = SIDE_BOX
        rr(d, SIDE_BOX, 10, PANEL, outline=GRID2)
        d.text((x0 + 20, y0 + 16), "STATE", font=F["tag"], fill=MUTED)
        big_label(d, g, x0 + 20, y0 + 60, "RANGE", GOLD, ease(lt / 0.6), "h1")
        big_label(d, g, x0 + 20, y0 + 150, "BOUND", WHITE, ease((lt - 0.2) / 0.6), "h1")
        d.text((x0 + 20, y0 + 270), "~2 weeks", font=F["h3"], fill=alpha(MUTED, ease((lt - 0.5) / 0.5)))
        rr(d, [x0 + 20, y0 + 340, x1 - 20, y0 + 440], 8, alpha(PANEL2, ease((lt - 2.5) / 0.6)), outline=alpha(GRID2, 1))
        d.text((x0 + 36, y0 + 356), "surface: quiet", font=F["sm"], fill=alpha(MUTED, ease((lt - 2.5) / 0.6)))
        d.text((x0 + 36, y0 + 392), "positioning: NOT quiet", font=F["sm"], fill=alpha(GOLD, ease((lt - 4.5) / 0.6)))
        caption(d, g, t)
    elif p == 2:  # players
        topbar(d, g, t, u); ticker(d, t, u)
        chart(d, g, CHART_BOX, t, title="XAUUSD · 1H", level=False)
        positioning_panel(d, g, SIDE_BOX, t, ease(lt / 2.5))
        big_label(d, g, 70, 150, "SIGNAL 1 · THE BIG PLAYERS", WHITE, ease(lt / 0.6), "h2")
        caption(d, g, t)
    elif p == 3:  # gamma level
        topbar(d, g, t, u); ticker(d, t, u)
        chart(d, g, CHART_BOX, t, title="XAUUSD · 1H · GC FUTURES", level=True, level_u=ease((lt - 1.0) / 1.6))
        gamma_panel(d, g, SIDE_BOX, t, ease(lt / 2.0), highlight=lt > 4)
        big_label(d, g, 70, 150, "SIGNAL 2 · THE OPTIONS MARKET", WHITE, ease(lt / 0.6), "h2")
        caption(d, g, t)
    elif p == 4:  # put-heavy above price
        topbar(d, g, t, u); ticker(d, t, u)
        px, py = chart(d, g, CHART_BOX, t, title="XAUUSD · 1H · GC FUTURES", level=True, wall=True)
        gamma_panel(d, g, SIDE_BOX, t, 1.0, highlight=True)
        big_label(d, g, 70, 150, "PUT-HEAVY LEVEL ABOVE PRICE", WHITE, ease(lt / 0.6), "h2")
        if lt > 7:
            v = ease((lt - 7) / 0.8); ly = py(LEVEL); xx = 1000
            d.line([(xx, ly + 170), (xx, ly - 90 * v)], fill=alpha(GREEN, v), width=7)
            g.line([(xx, ly + 170), (xx, ly - 90 * v)], fill=(20, 90, 60), width=16)
            d.polygon([(xx - 22, ly - 80 * v), (xx + 22, ly - 80 * v), (xx, ly - 125 * v)], fill=alpha(GREEN, v))
            d.text((xx + 40, ly - 150), "SHOULD BREAK UP EASILY", font=F["h3"], fill=alpha(GREEN, v))
            d.text((xx + 40, ly - 105), "dealer hedges can push through", font=F["sm"], fill=alpha(MUTED, v))
        caption(d, g, t)
    elif p == 5:  # rejection
        topbar(d, g, t, u); ticker(d, t, u)
        zu = ease_io(lt / 2.0)
        px, py = chart(d, g, CHART_BOX, t, title="XAUUSD · 1H · ZOOM", level=True, zoom_u=zu, rejections=lt > 2.5, wall=True)
        x0, y0, x1, y1 = SIDE_BOX
        rr(d, SIDE_BOX, 10, PANEL, outline=GRID2)
        d.text((x0 + 20, y0 + 16), "ORDER FLOW READ", font=F["tag"], fill=MUTED)
        big_label(d, g, x0 + 20, y0 + 60, "REJECTING", RED, ease((lt - 2.5) / 0.6), "h1")
        d.text((x0 + 20, y0 + 150), "under 4,150 · again and again", font=F["h3"], fill=alpha(WHITE, ease((lt - 3) / 0.6)))
        rows = [("hedgers & buyers", "orders being filled"), ("someone, somewhere", "feeding sell positions"), ("the buying", "is being absorbed")]
        for k, (a, b) in enumerate(rows):
            yy = y0 + 240 + k * 120; uu = ease((lt - 7 - k * 3.5) / 0.6)
            rr(d, [x0 + 20, yy, x1 - 20, yy + 96], 8, alpha(PANEL2, uu), outline=alpha(RED, uu * 0.6))
            d.text((x0 + 36, yy + 14), a, font=F["sm"], fill=alpha(MUTED, uu))
            d.text((x0 + 36, yy + 50), b, font=F["h3"], fill=alpha(RED if k == 2 else WHITE, uu))
        if lt > 19:
            v = ease((lt - 19) / 0.6)
            d.text((x0 + 20, y1 - 60), "a level that should give way is holding", font=F["sm"], fill=alpha(GOLD, v))
        caption(d, g, t)
    elif p == 6:  # regime
        topbar(d, g, t, u); ticker(d, t, u)
        chart(d, g, CHART_BOX, t, title="XAUUSD · 1H", level=True)
        macro_panel(d, g, SIDE_BOX, t, ease(lt / 2.5))
        big_label(d, g, 70, 150, "SIGNAL 3 · THE REGIME", WHITE, ease(lt / 0.6), "h2")
        if lt > 6:
            v = ease((lt - 6) / 0.7)
            big_label(d, g, 70, 720, "BEARISH REGIME", RED, v, "h1")
        caption(d, g, t)
    elif p == 7:  # summary
        topbar(d, g, t, u); ticker(d, t, u)
        chart(d, g, (40, 110, 900, 870), t, title="XAUUSD · 1H", level=True, zoom_u=1.0, rejections=True, wall=True)
        x0, y0, x1, y1 = (930, 110, 1880, 870)
        rr(d, (x0, y0, x1, y1), 10, PANEL, outline=GRID2)
        d.text((x0 + 24, y0 + 16), "PUTTING IT TOGETHER", font=F["tag"], fill=MUTED)
        rows = [("REGIME", "bearish"), ("OPTION GAMMA", "a level that should break easily is holding price down"), ("POSITIONING", "first signs of new shorts coming in")]
        for k, (a, b) in enumerate(rows):
            yy = y0 + 80 + k * 230; uu = ease((lt - 1.5 - k * 4.2) / 0.6)
            big_label(d, g, x0 + 30, yy - 10, str(k + 1), GOLD, uu, "num")
            d.text((x0 + 160, yy + 20), a, font=F["h2"], fill=alpha(WHITE, uu))
            d.text((x0 + 160, yy + 90), b, font=F["body"], fill=alpha(MUTED, uu))
            d.ellipse([x1 - 90, yy + 40, x1 - 40, yy + 90], fill=alpha(RED, uu))
            d.polygon([(x1 - 78, yy + 58), (x1 - 52, yy + 58), (x1 - 65, yy + 78)], fill=alpha(WHITE, uu))
        caption(d, g, t)
    elif p == 8:  # conclusion
        topbar(d, g, t, u); ticker(d, t, u)
        chart(d, g, CHART_BOX, t, title="XAUUSD · 1H · OUTLOOK", level=True, zoom_u=1.0, wall=True, breakdown=ease((lt - 2.0) / 1.6))
        x0, y0, x1, y1 = SIDE_BOX
        rr(d, SIDE_BOX, 10, PANEL, outline=GRID2)
        d.text((x0 + 20, y0 + 16), "MY VIEW", font=F["tag"], fill=MUTED)
        big_label(d, g, x0 + 20, y0 + 60, "GOLD", WHITE, ease(lt / 0.6), "h1")
        big_label(d, g, x0 + 20, y0 + 150, "LOWER", RED, ease((lt - 0.2) / 0.6), "h1")
        d.text((x0 + 20, y0 + 270), "from around", font=F["sm"], fill=alpha(MUTED, ease((lt - 1) / 0.5)))
        big_label(d, g, x0 + 20, y0 + 300, "4,150", GOLD, ease((lt - 1) / 0.5), "hero")
        d.text((x0 + 20, y0 + 450), "expect the price to fall through", font=F["h3"], fill=alpha(WHITE, ease((lt - 3) / 0.6)))
        d.text((x0 + 20, y0 + 500), "this is the level I'm watching", font=F["sm"], fill=alpha(MUTED, ease((lt - 6) / 0.6)))
        caption(d, g, t)
    else:  # outro
        v = ease(lt / 0.8)
        wolf_mark(d, g, W / 2, 300, 130, GOLD, v)
        big_label(d, g, W / 2 - tw(d, "ANONYMOUS WOLF TRADER", F["h1"]) / 2, 470, "ANONYMOUS WOLF TRADER", WHITE, v)
        d.rectangle([W / 2 - 240 * v, 565, W / 2 + 240 * v, 569], fill=GOLD)
        s1 = "SUBSCRIBE FOR THE NEXT GOLD UPDATE"
        pw_ = tw(d, s1, F["h3"]) / 2 + 40
        rr(d, [W / 2 - pw_, 600, W / 2 + pw_, 660], 30, alpha(GOLD, ease((lt - 0.6) / 0.6)))
        d.text((W / 2 - tw(d, s1, F["h3"]) / 2, 612), s1, font=F["h3"], fill=alpha((20, 16, 6), ease((lt - 0.6) / 0.6)))
        s2 = "This is my own analysis and not financial advice."; s3 = "Trade your own plan. Manage your risk."
        d.text((W / 2 - tw(d, s2, F["body"]) / 2, 700), s2, font=F["body"], fill=alpha(MUTED, ease((lt - 1.4) / 0.6)))
        d.text((W / 2 - tw(d, s3, F["body"]) / 2, 745), s3, font=F["body"], fill=alpha(MUTED, ease((lt - 2.0) / 0.6)))
        ticker(d, t, v)

    out = composite(base, glow, 1.0, 41)
    # subtle scanlines
    out[::4] = (out[::4].astype(np.int16) - 6).clip(0, 255).astype(np.uint8)
    gf = min(1.0, t / 0.8, max(0.0, (TOTAL - t) / 1.2))
    if gf < 1: out = (out * gf).astype(np.uint8)
    return out

def main():
    import subprocess
    f0, f1 = int(T0 * FPS), int(T1 * FPS)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", OUT]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(f0, f1):
        pr.stdin.write(render(f / FPS).tobytes())
        if f % 150 == 0: print(f"frame {f}/{f1}", flush=True)
    pr.stdin.close(); pr.wait(); print("done", OUT)

if __name__ == "__main__":
    main()
