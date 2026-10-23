#!/usr/bin/env python3
"""Anonymous Wolf Trader — engine v2: holographic quant motion graphics.
Usage: ENV... python3 engine2.py timing.json out.mp4 [start_sec end_sec]
Requires timing.json from align.py (sentences, scenes, words). Scenes come from a scene plan
module (env SCENES=<module>) exposing PLAN = [ {para, template, **params}, ... ].
Templates: hero_chart, split, impact, quote, timeline, chain, cards, bumper, outro.
"""
import sys, os, json, math, random, importlib.util
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1920, 1080, 30
T = json.load(open(sys.argv[1])); OUT = sys.argv[2]
T0 = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
TOTAL = T["scenes"][-1]["end"] + 2.0
T1 = float(sys.argv[4]) if len(sys.argv) > 4 else TOTAL
E = os.environ.get

# ---------- palette & fonts ----------
BG = (6, 9, 15); PANEL = (10, 14, 23); PANEL2 = (15, 20, 31); GRID = (20, 27, 42); GRID2 = (32, 41, 60)
GOLD = (242, 193, 78); GOLD2 = (255, 226, 150); RED = (255, 77, 77); GREEN = (46, 230, 166); CYAN = (70, 200, 255)
WHITE = (238, 241, 248); MUTED = (125, 136, 160); DIM = (70, 80, 100)
FD = "/usr/share/fonts/opentype/inter/"
def font(sz, w="Bold", d=True): return ImageFont.truetype(FD + ("InterDisplay-" if d else "Inter-") + w + ".otf", sz)
F = {"hero": font(170, "ExtraBold"), "h1": font(88, "ExtraBold"), "h2": font(56, "Bold"), "h3": font(36, "SemiBold"),
     "quote": font(64, "Bold"), "body": font(30, "Medium", False), "cap": font(38, "SemiBold", False), "sm": font(22, "Medium", False),
     "tag": font(20, "SemiBold", False), "tiny": font(17, "Medium", False), "num": font(220, "ExtraBold")}

def ease(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3
def ease_io(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
def mix(a, b, u): return tuple(int(a[i] + (b[i] - a[i]) * u) for i in range(3))
def alpha(c, u): return mix(BG, c, max(0.0, min(1.0, u)))
def tw(d, s, f): return d.textlength(s, font=f)
def rr(d, box, r, fill, outline=None, width=1): d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)

# ---------- data ----------
LEVEL = float(E("LEVEL", "4132")); LEVEL2 = float(E("LEVEL2", "0")) or None
random.seed(11)
C = []
if os.path.exists("candles.json"):
    _d = json.load(open("candles.json"))["candles"][-200:]
    C = [(c["o"], c["h"], c["l"], c["c"], c["v"]) for c in _d]
if len(C) < 50:
    p = 4118.0
    for i in range(200):
        o = p; c = min(LEVEL - 2 - random.random() * 6, max(4086 + random.random() * 6, o + random.gauss(0, 6.5)))
        C.append((o, max(o, c) + abs(random.gauss(0, 4)), min(o, c) - abs(random.gauss(0, 4)), c, random.random() * 100)); p = c
N = len(C)
_lo = min(c[2] for c in C); _hi = max(c[1] for c in C)
if LEVEL2: _lo = min(_lo, LEVEL2)
_pad = (_hi - _lo) * 0.12
PMIN, PMAX = _lo - _pad, max(_hi, LEVEL) + _pad

# ---------- scene plan ----------
spec = importlib.util.spec_from_file_location("plan", E("SCENES", "plan") + ".py"); _m = importlib.util.module_from_spec(spec); spec.loader.exec_module(_m)
PLAN = {s["para"]: s for s in _m.PLAN}
SC = T["scenes"]; SENTS = T["sentences"]; WORDS = T.get("words", [])
def scene_at(t):
    for s in SC:
        if s["start"] <= t < s["end"]: return s
    return SC[0] if t < SC[0]["start"] else SC[-1]

# ---------- particle / background system ----------
rng = np.random.default_rng(5)
PARTS = np.stack([rng.uniform(0, W, 220), rng.uniform(0, H, 220), rng.uniform(0.3, 1.0, 220), rng.uniform(0, 6.28, 220)], 1)
STREAMS = [(rng.uniform(0, W), rng.uniform(0.4, 1.6), rng.uniform(80, 260), rng.uniform(0, 1)) for _ in range(26)]
_YY, _XX = np.mgrid[0:H, 0:W]
_R = np.sqrt((_XX - W * 0.5) ** 2 + (_YY - H * 0.45) ** 2) / (W * 0.75)
_RAD = np.clip(1.25 - _R, 0.35, 1.0)[..., None].astype(np.float32)
_XF = _XX[0].astype(np.float32)
_BGCACHE = {}
def background(t, drift=1.0, tint=None):
    key = tuple(tint or (18, 24, 40))
    if key not in _BGCACHE:
        _BGCACHE[key] = np.clip(np.array(key, np.float32)[None, None, :] * _RAD, 0, 255).astype(np.uint8)
    pil = Image.fromarray(_BGCACHE[key].copy()); d = ImageDraw.Draw(pil)
    # perspective grid floor, slowly scrolling
    hz = 640; off = (t * 40 * drift) % 48
    for i in range(-18, 19):
        d.line([(W / 2 + i * 52, hz), (W / 2 + i * 480, H + 200)], fill=(13, 18, 30), width=1)
    y = hz; k = 0
    while y < H:
        y = hz + (k * k * 2.2) + off * (1 + k * 0.08); d.line([(0, y), (W, y)], fill=(14, 19, 31), width=1); k += 1
    # vertical data streams
    for (x, sp, ln, ph) in STREAMS:
        y0 = ((t * 140 * sp + ph * H) % (H + ln)) - ln
        d.line([(x, y0), (x, y0 + ln)], fill=(18, 26, 42), width=2)
        d.rectangle([x - 1, y0 + ln - 6, x + 1, y0 + ln], fill=(60, 55, 30))
    # particles
    for px, py, z, ph in PARTS:
        x = (px + math.sin(t * 0.2 + ph) * 20 * z) % W; y = (py - t * 12 * z) % H
        s = 1 + z * 1.6; c = int(40 + 90 * z * (0.6 + 0.4 * math.sin(t * 2 + ph)))
        d.ellipse([x - s, y - s, x + s, y + s], fill=(c, int(c * 0.85), int(c * 0.4)))
    # light sweep
    sx = ((t * 160) % (W + 800)) - 400
    arr = np.asarray(pil).astype(np.int16)
    band = (np.exp(-((_XF - sx) / 140.0) ** 2) * 10)
    arr += (band[None, :, None] * np.array([1.0, 0.85, 0.45])[None, None, :]).astype(np.int16)
    return np.clip(arr, 0, 255).astype(np.uint8)

_VIG = {}
def vignette(arr, k=0.5):
    if k not in _VIG:
        v = 1 - k * (((_XX - W / 2) / (W / 2)) ** 2 + ((_YY - H / 2) / (H / 2)) ** 2) ** 1.3
        _VIG[k] = np.clip(v, 0.25, 1)[..., None].astype(np.float32)
    return (arr.astype(np.float32) * _VIG[k]).astype(np.uint8)

def glow_composite(base, glow, k=51, strength=1.0):
    b = np.asarray(base).astype(np.int16)
    g = np.asarray(glow)
    small = cv2.resize(g, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    small = cv2.GaussianBlur(small, (max(3, (k // 4) | 1), max(3, (k // 4) | 1)), 0)
    g = (cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32) * strength).astype(np.int16)
    return np.clip(b + g, 0, 255).astype(np.uint8)

# ---------- chart (drawn flat, then camera-warped) ----------
def draw_chart(w, h, t, frac=1.0, zoom=0.0, level=True, level2=False, rejections=False, breakdown=0.0, entries=(), title="", labels=True):
    """Returns (RGB image, glow image) of size w x h with transparent-ish dark panel."""
    img = Image.new("RGB", (w, h), (0, 0, 0)); d = ImageDraw.Draw(img)
    glow = Image.new("RGB", (w, h), (0, 0, 0)); g = ImageDraw.Draw(glow)
    rr(d, [0, 0, w - 1, h - 1], 16, (9, 13, 22), outline=(40, 50, 72), width=2)
    a = int((N - 56) * zoom); vis = list(range(a, N)); vis = vis[:max(2, int(len(vis) * frac))]
    lo_p = PMIN + (min(c[2] for c in C[a:]) - 8 - PMIN) * zoom; hi_p = PMAX - (PMAX - max(max(c[1] for c in C[a:]), LEVEL) - 8) * zoom
    if level2 and LEVEL2: lo_p = min(lo_p, LEVEL2 - 8)
    cw = (w - 150) / max(len(range(a, N)), 1)
    px = lambda i: 24 + (i - a) * cw
    py = lambda p: h - 70 - (p - lo_p) / (hi_p - lo_p) * (h - 120)
    step = 20 if (hi_p - lo_p) > 90 else 10; p = math.ceil(lo_p / step) * step
    while p < hi_p:
        y = py(p); d.line([(14, y), (w - 110, y)], fill=(20, 27, 42)); d.text((w - 96, y - 11), f"{p:,.0f}", font=F["sm"], fill=DIM); p += step
    if title: d.text((24, 14), title, font=F["tag"], fill=MUTED)
    vmax = max(c[4] for c in C) or 1
    for i in vis:
        o, hi, lo, c, v = C[i]; x = px(i); hh = v / vmax * 60
        d.rectangle([x - cw * 0.3, h - 12 - hh, x + cw * 0.3, h - 12], fill=(18, 25, 38) if c >= o else (34, 20, 26))
    for i in vis:
        o, hi, lo, c, v = C[i]; x = px(i); col = GREEN if c >= o else RED
        d.line([(x, py(hi)), (x, py(lo))], fill=mix((0, 0, 0), col, 0.7), width=2)
        d.rectangle([x - cw * 0.34, py(max(o, c)), x + cw * 0.34, py(min(o, c)) + 1], fill=col)
    pts = [(px(i), py(C[i][3])) for i in vis]; g.line(pts, fill=(70, 55, 18), width=7)
    def hline(price, col, lab):
        y = py(price)
        for x in range(14, w - 110, 26): d.line([(x, y), (x + 15, y)], fill=col, width=3)
        g.line([(14, y), (w - 110, y)], fill=mix((0, 0, 0), col, 0.4), width=10)
        if labels and lab:
            lw = tw(d, lab, F["tag"]); rr(d, [24, y - 40, 24 + lw + 28, y - 8], 6, (14, 18, 28), outline=col); d.text((38, y - 34), lab, font=F["tag"], fill=col)
    if level: hline(LEVEL, RED, E("LEVEL_LABEL", ""))
    if level2 and LEVEL2: hline(LEVEL2, GOLD, E("LEVEL2_LABEL", ""))
    for (price, col, lab) in entries: hline(price, col, lab)
    if rejections:
        y = py(LEVEL); hits = [i for i in vis if C[i][1] >= LEVEL - 4 and C[i][3] < LEVEL][-6:]
        for i in hits:
            x = px(i); d.ellipse([x - 11, y - 11, x + 11, y + 11], outline=RED, width=2); g.ellipse([x - 13, y - 13, x + 13, y + 13], outline=(120, 30, 30), width=4)
    if pts:
        lx, ly = pts[-1]; d.ellipse([lx - 7, ly - 7, lx + 7, ly + 7], fill=WHITE); g.ellipse([lx - 12, ly - 12, lx + 12, ly + 12], fill=(100, 90, 50))
        pr = f"{C[vis[-1]][3]:,.1f}"; rr(d, [w - 106, ly - 15, w - 10, ly + 15], 5, GOLD); d.text((w - 100, ly - 11), pr, font=F["sm"], fill=(20, 16, 6))
        if breakdown > 0:
            tgt = LEVEL2 if (LEVEL2 and level2) else lo_p + (hi_p - lo_p) * 0.15
            ex, ey = lx + 180 * breakdown, ly + (py(tgt) - ly) * breakdown
            d.line([(lx, ly), (ex, ey)], fill=RED, width=8); g.line([(lx, ly), (ex, ey)], fill=(120, 30, 30), width=18)
            ang = math.atan2(ey - ly, ex - lx); ah = 30
            d.polygon([(ex, ey), (ex - ah * math.cos(ang - .45), ey - ah * math.sin(ang - .45)), (ex - ah * math.cos(ang + .45), ey - ah * math.sin(ang + .45))], fill=RED)
    return img, glow, (px, py)

def camera(img_np, t, tilt=0.10, push=0.0, drift=1.0, cx=None, cy=None, scale=1.0):
    """Perspective tilt + slow drift/push. img_np is a full-frame canvas; returns warped canvas."""
    h, w = img_np.shape[:2]
    s = scale * (1.0 + 0.04 * push)
    dx = math.sin(t * 0.21) * 14 * drift; dy = math.cos(t * 0.17) * 9 * drift
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    k = tilt * 0.5
    dst = np.float32([[w * k * 0.5 + dx, h * k * 0.35 + dy], [w - w * k * 0.5 + dx, dy], [w + dx, h + dy], [dx, h - h * k * 0.35 + dy]])
    M = cv2.getPerspectiveTransform(src, dst)
    cxx = cx if cx is not None else w / 2; cyy = cy if cy is not None else h / 2
    S = np.float32([[s, 0, cxx * (1 - s)], [0, s, cyy * (1 - s)], [0, 0, 1]])
    return cv2.warpPerspective(img_np, S @ M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))

def reflection(canvas, y_floor, strength=0.22):
    """Mirror the region above y_floor below it, faded, for a glass-floor feel."""
    h = canvas.shape[0]; band = min(h - y_floor, 220)
    if band <= 10: return canvas
    src = canvas[y_floor - band:y_floor][::-1].astype(np.float32)
    fade = np.linspace(strength, 0.0, band)[:, None, None]
    src = cv2.GaussianBlur(src, (0, 0), 2) * fade
    canvas[y_floor:y_floor + band] = np.clip(canvas[y_floor:y_floor + band] + src, 0, 255).astype(np.uint8)
    return canvas

def paste_np(canvas, img, x, y, alpha_mask=None):
    h, w = img.shape[:2]; x, y = int(x), int(y)
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0: return canvas
    sub = img[y0 - y:y1 - y, x0 - x:x1 - x]
    if alpha_mask is None:
        m = (sub.sum(2) > 20)[..., None]
        canvas[y0:y1, x0:x1] = np.where(m, sub, canvas[y0:y1, x0:x1])
    else:
        am = alpha_mask[y0 - y:y1 - y, x0 - x:x1 - x][..., None]
        canvas[y0:y1, x0:x1] = (canvas[y0:y1, x0:x1] * (1 - am) + sub * am).astype(np.uint8)
    return canvas

# ---------- HUD, captions ----------
def hud(d, g, t, u=1.0):
    rr(d, [0, 0, W, 76], 0, (8, 11, 18)); d.line([(0, 76), (W, 76)], fill=GRID2)
    wolf(d, g, 58, 38, 22, GOLD, u)
    d.text((100, 18), "ANONYMOUS WOLF TRADER", font=F["h3"], fill=alpha(WHITE, u))
    d.text((640, 30), E("VDATE", "GOLD UPDATE"), font=F["tag"], fill=alpha(MUTED, u))
    p = C[-1][3] + math.sin(t * 7.3) * 0.6; s = f"{p:,.2f}"
    d.text((W - 60 - tw(d, s, F["h3"]), 16), s, font=F["h3"], fill=alpha(GOLD, u)); g.text((W - 60 - tw(d, s, F["h3"]), 16), s, font=F["h3"], fill=(70, 55, 18))
    d.text((W - 330, 26), "GOLD SPOT ≈", font=F["tag"], fill=alpha(MUTED, u))
    d.ellipse([W - 354, 32, W - 344, 42], fill=alpha(GREEN if int(t * 2) % 2 == 0 else (20, 90, 60), u))

def wolf(d, g, cx, cy, s, col=GOLD, u=1.0):
    pts = [(-0.95, -0.9), (-0.55, -0.25), (-0.75, 0.15), (-0.35, 0.55), (0, 0.95), (0.35, 0.55), (0.75, 0.15), (0.55, -0.25), (0.95, -0.9), (0.45, -0.55), (0, -0.4), (-0.45, -0.55)]
    poly = [(cx + x * s, cy + y * s) for x, y in pts]; c = alpha(col, u)
    d.line(poly + [poly[0]], fill=c, width=max(2, int(s / 12))); g.line(poly + [poly[0]], fill=mix((0, 0, 0), col, 0.5 * u), width=max(4, int(s / 6)))
    for ex in (-0.33, 0.33):
        e = [(cx + (ex - .14) * s, cy - .05 * s), (cx + ex * s, cy - .2 * s), (cx + (ex + .14) * s, cy - .05 * s)]; d.line(e, fill=c, width=max(2, int(s / 16)))
    d.polygon([(cx - .1 * s, cy + .55 * s), (cx + .1 * s, cy + .55 * s), (cx, cy + .72 * s)], fill=c)

def caption(d, g, t, y=None):
    cur = next((s for s in SENTS if s["start"] <= t < s["end"]), None)
    if not cur: return
    si = SENTS.index(cur); ws = [w for w in WORDS if w["sent"] == si]
    if not ws: return
    f = F["cap"]; words = [w["w"] for w in ws]
    lines, line = [], []
    for w in words:
        if tw(d, " ".join(line + [w]), f) > 1300 and line: lines.append(line); line = [w]
        else: line.append(w)
    if line: lines.append(line)
    # find the line with the active word; show that line and the next one only
    k0 = 0; act_line = 0
    for li, l in enumerate(lines):
        if any(ws[k0 + j]["start"] <= t for j in range(len(l))): act_line = li
        k0 += len(l)
    first = min(act_line, max(0, len(lines) - 2)); lines_show = lines[first:first + 2]
    k = sum(len(l) for l in lines[:first])
    lh = 50; y0 = (y if y is not None else H - 110 - lh * len(lines_show))
    maxw = max(tw(d, " ".join(l), f) for l in lines_show)
    rr(d, [(W - maxw) / 2 - 26, y0 - 12, (W + maxw) / 2 + 26, y0 + lh * len(lines_show) + 6], 10, (7, 10, 16), outline=GRID2)
    for li, l in enumerate(lines_show):
        x = (W - tw(d, " ".join(l), f)) / 2; yy = y0 + li * lh
        for w in l:
            wd = ws[k]; active = wd["start"] <= t < wd["end"] + 0.05; done = t >= wd["end"]
            col = GOLD if active else (WHITE if done else (150, 158, 178))
            d.text((x, yy), w, font=f, fill=col)
            if active: g.text((x, yy), w, font=f, fill=(90, 70, 20))
            x += tw(d, w + " ", f); k += 1

def big(d, g, x, y, s, col, u, f="h1", center=False):
    if center: x = x - tw(d, s, F[f]) / 2
    d.text((x, y), s, font=F[f], fill=alpha(col, u)); g.text((x, y), s, font=F[f], fill=mix((0, 0, 0), col, 0.35 * u))

def fit_font(d, text, maxw, base="h3"):
    order = ["h1", "h2", "h3", "body", "sm", "tiny"]; i = order.index(base)
    while i < len(order) - 1 and tw(d, text, F[order[i]]) > maxw: i += 1
    return order[i]

def plate(d, box, u, col=None):
    rr(d, box, 14, alpha((8, 11, 18), u * 0.92), outline=alpha(col or GRID2, u))

# ---------- templates ----------
def tpl_hero_chart(P, t, lt, s, canvas, d, g):
    """Full-bleed floating chart with camera push; headline lower-left."""
    dur = s["end"] - s["start"]
    img, gl, _ = draw_chart(1500, 700, t, frac=P.get("frac", 1.0) if not P.get("build") else ease(lt / P.get("build", 5)),
                            zoom=P.get("zoom", 0.0), level=P.get("level", True), level2=P.get("level2", False),
                            rejections=P.get("rejections", False) and lt > P.get("rej_at", 2),
                            breakdown=ease((lt - P.get("break_at", 99)) / 1.5) if P.get("break_at") else 0.0,
                            entries=[e for e in P.get("entries", []) if lt > e[3]] and [(e[0], e[1], e[2]) for e in P.get("entries", []) if lt > e[3]], title=P.get("title", ""))
    frame = np.zeros((H, W, 3), np.uint8); frame = paste_np(frame, np.asarray(img), 210, 215)
    gframe = np.zeros((H, W, 3), np.uint8); gframe = paste_np(gframe, np.asarray(gl), 210, 215)
    push = ease_io(lt / dur); warped = camera(frame, t, tilt=0.12, push=push * 0.8); gw = camera(gframe, t, tilt=0.12, push=push * 0.8)
    canvas = np.where(warped.sum(2, keepdims=True) > 20, warped, canvas); canvas = reflection(canvas, 915)
    canvas = glow_composite(canvas, gw, 61, 1.0)
    pil = Image.fromarray(canvas); d = ImageDraw.Draw(pil); g2 = ImageDraw.Draw(Image.new("RGB", (W, H), (0, 0, 0)))
    if P.get("headline"):
        v = ease((lt - 0.3) / 0.6); lines = P["headline"].split("|"); y = 96
        for i, l in enumerate(lines):
            col = GOLD if i == len(lines) - 1 and len(lines) > 1 else WHITE
            lw = tw(d, l, F["h3"]); plate(d, [80, y - 6, 80 + lw + 44, y + 50], v); d.rectangle([80, y - 6, 86, y + 50], fill=alpha(col, v))
            big(d, g2, 104, y, l, col, v, "h3"); y += 62
    return pil

def tpl_split(P, t, lt, s, canvas, d, g):
    """Chart left (tilted), animated info panel right (rows slide in)."""
    img, gl, _ = draw_chart(1180, 740, t, zoom=P.get("zoom", 0.0), level=P.get("level", True), level2=P.get("level2", False),
                            rejections=P.get("rejections", False) and lt > 2, title=P.get("title", ""),
                            entries=[(e[0], e[1], e[2]) for e in P.get("entries", []) if lt > e[3]])
    frame = np.zeros((H, W, 3), np.uint8); frame = paste_np(frame, np.asarray(img), 60, 150)
    gframe = np.zeros((H, W, 3), np.uint8); gframe = paste_np(gframe, np.asarray(gl), 60, 150)
    warped = camera(frame, t, tilt=0.16, drift=0.6); gw = camera(gframe, t, tilt=0.16, drift=0.6)
    canvas = np.where(warped.sum(2, keepdims=True) > 20, warped, canvas); canvas = reflection(canvas, 900, 0.18)
    canvas = glow_composite(canvas, gw, 61)
    pil = Image.fromarray(canvas); d = ImageDraw.Draw(pil); g2 = ImageDraw.Draw(Image.new("RGB", (W, H), (0, 0, 0)))
    x0, y0, x1, y1 = 1300, 140, 1860, 900
    plate(d, [x0, y0, x1, y1], ease(lt / 0.5))
    d.text((x0 + 24, y0 + 18), P.get("panel_title", ""), font=F["tag"], fill=MUTED)
    if P.get("headline"): big(d, g2, 90, 100, P["headline"], WHITE, ease(lt / 0.5), "h2")
    rows = P.get("rows", []); yy = y0 + 70
    for i, r in enumerate(rows):
        at = r.get("at", 1 + i * 2.5); v = ease((lt - at) / 0.5); col = r.get("col", WHITE)
        slide = int((1 - v) * 60)
        rr(d, [x0 + 20 + slide, yy, x1 - 20 + slide, yy + r.get("h", 110)], 10, alpha(PANEL2, v), outline=alpha(col, v * 0.6))
        d.rectangle([x0 + 20 + slide, yy, x0 + 26 + slide, yy + r.get("h", 110)], fill=alpha(col, v))
        d.text((x0 + 44 + slide, yy + 14), r.get("k", ""), font=F["sm"], fill=alpha(MUTED, v))
        big(d, g2, x0 + 44 + slide, yy + 44, r.get("v", ""), col, v, fit_font(d, r.get("v", ""), x1 - x0 - 90, "h3"))
        if r.get("sub"): d.text((x0 + 44 + slide, yy + 86), r["sub"], font=F["tiny"], fill=alpha(MUTED, v))
        yy += r.get("h", 110) + 16
    if P.get("footer"):
        v = ease((lt - P.get("footer_at", 8)) / 0.6); big(d, g2, x0 + 24, y1 - 70, P["footer"], GOLD, v, fit_font(d, P["footer"], x1 - x0 - 48, "h3"))
    return pil

def tpl_impact(P, t, lt, s, canvas, d, g):
    """Full-screen number/word impact card with count-up."""
    pil = Image.fromarray(canvas); d = ImageDraw.Draw(pil); g2 = ImageDraw.Draw(Image.new("RGB", (W, H), (0, 0, 0)))
    v = ease(lt / 0.7); kicker = P.get("kicker", ""); val = P.get("value", ""); sub = P.get("sub", "")
    if kicker: d.text(((W - tw(d, kicker, F["h3"])) / 2, 270), kicker, font=F["h3"], fill=alpha(MUTED, v))
    if P.get("count"):
        a, b = P["count"]; num = a + (b - a) * ease(lt / 1.6); txt = P.get("fmt", "{:,.0f}").format(num)
    else: txt = val
    r = 260 + 160 * ease(lt / 1.2); d.ellipse([W / 2 - r, 420 - r * 0.55, W / 2 + r, 420 + r * 0.55], outline=alpha(GOLD, (1 - ease(lt / 1.2)) * 0.8), width=3)
    big(d, g2, W / 2, 330, txt, P.get("col", GOLD), v, "num", center=True)
    if sub:
        v2 = ease((lt - 1.2) / 0.6)
        for i, l in enumerate(sub.split("|")):
            big(d, g2, W / 2, 600 + i * 70, l, WHITE if i == 0 else MUTED, v2, "h2" if i == 0 else "h3", center=True)
    return pil

def tpl_quote(P, t, lt, s, canvas, d, g):
    """Kinetic typography: the paragraph's key sentence builds word by word in sync with the voice."""
    pil = Image.fromarray(canvas); d = ImageDraw.Draw(pil); g2 = ImageDraw.Draw(Image.new("RGB", (W, H), (0, 0, 0)))
    sent = next((x for x in SENTS if x["para"] == s["para"] and x["start"] <= t < x["end"]), None)
    if sent is None:
        cands = [x for x in SENTS if x["para"] == s["para"] and x["start"] <= t]
        sent = cands[-1] if cands else next((x for x in SENTS if x["para"] == s["para"]), None)
    if sent is None: return pil
    idx = SENTS.index(sent); ws = [w for w in WORDS if w["sent"] == idx]
    f = F["quote"]; lines, line = [], []
    for w in ws:
        if tw(d, " ".join([x["w"] for x in line + [w]]), f) > 1500 and line: lines.append(line); line = [w]
        else: line.append(w)
    if line: lines.append(line)
    total_h = len(lines) * 84; y = (H - total_h) / 2 - 20
    for l in lines:
        x = (W - tw(d, " ".join([x["w"] for x in l]), f)) / 2
        for w in l:
            v = ease((t - w["start"]) / 0.25)
            hot = any(ch.isdigit() for ch in w["w"]) or w["w"].strip(",.").upper() in P.get("hot", [])
            col = GOLD if hot else WHITE
            d.text((x, y + (1 - v) * 18), w["w"], font=f, fill=alpha(col, v))
            if v > 0.9 and hot: g2.text((x, y), w["w"], font=f, fill=(90, 70, 20))
            x += tw(d, w["w"] + " ", f)
        y += 84
    if P.get("kicker"):
        d.text(((W - tw(d, P["kicker"], F["tag"])) / 2, (H - total_h) / 2 - 80), P["kicker"], font=F["tag"], fill=alpha(MUTED, ease(lt / 0.5)))
    return pil

def tpl_timeline(P, t, lt, s, canvas, d, g):
    """Month bars (seasonality) + callouts."""
    pil = Image.fromarray(canvas); d = ImageDraw.Draw(pil); g2 = ImageDraw.Draw(Image.new("RGB", (W, H), (0, 0, 0)))
    x0, y0, x1, y1 = 100, 120, 1820, 840; plate(d, [x0, y0, x1, y1], ease(lt / 0.5))
    d.text((x0 + 24, y0 + 16), P.get("title", ""), font=F["tag"], fill=MUTED)
    months = P.get("labels", ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]); vals = P.get("vals", [0.7, 0.6, 0.1, 0.2, 0.0, -0.1, 0.4, 0.5, 0.3, -0.6, 0.6, 0.6])
    hi = set(P.get("highlight", [])); neg = set(P.get("negative", []))
    bw = (x1 - x0 - 120) / len(months); base_y = y0 + 470
    for i, (m, v_) in enumerate(zip(months, vals)):
        vv = ease((lt - 0.5 - i * 0.12) / 0.5); xx = x0 + 60 + i * bw; hh = v_ * 280 * vv
        col = RED if i in neg else (GOLD if i in hi else mix(BG, GREEN, 0.6))
        d.rectangle([xx + 10, min(base_y, base_y - hh), xx + bw - 10, max(base_y, base_y - hh)], fill=alpha(col, vv))
        if i in hi or i in neg: g2.rectangle([xx + 10, min(base_y, base_y - hh), xx + bw - 10, max(base_y, base_y - hh)], fill=mix((0, 0, 0), col, 0.4))
        d.text((xx + bw / 2 - tw(d, m, F["sm"]) / 2, base_y + 14), m, font=F["sm"], fill=alpha(GOLD if i in hi else (RED if i in neg else DIM), vv))
    d.line([(x0 + 40, base_y), (x1 - 40, base_y)], fill=GRID2)
    for co in P.get("callouts", []):
        v = ease((lt - co["at"]) / 0.6); big(d, g2, co["x"], co["y"], co["text"], co.get("col", GOLD), v, co.get("f", "h3"))
    if P.get("note"): d.text((x0 + 60, y1 - 56), P["note"], font=F["sm"], fill=alpha(MUTED, ease((lt - P.get("note_at", 10)) / 0.6)))
    return pil

def tpl_chain(P, t, lt, s, canvas, d, g):
    """Cause → effect chain across the screen with connectors; optional sparkline pair."""
    pil = Image.fromarray(canvas); d = ImageDraw.Draw(pil); g2 = ImageDraw.Draw(Image.new("RGB", (W, H), (0, 0, 0)))
    if P.get("headline"): big(d, g2, 90, 110, P["headline"], WHITE, ease(lt / 0.5), "h2")
    items = P.get("items", []); n = len(items); bw = 360; gap = (W - 160 - n * bw) / max(n - 1, 1)
    for i, it in enumerate(items):
        v = ease((lt - it.get("at", 1 + i * 2)) / 0.5); x = 80 + i * (bw + gap); y = 380; col = it.get("col", WHITE)
        rise = (1 - v) * 40
        rr(d, [x, y + rise, x + bw, y + 200 + rise], 14, alpha(PANEL2, v), outline=alpha(col, v * 0.8))
        big(d, g2, x + 24, y + 30 + rise, it["t"], col, v, fit_font(d, it["t"], bw - 48, "h3"))
        if it.get("sub"): d.text((x + 24, y + 120 + rise), it["sub"], font=F["sm"], fill=alpha(MUTED, v))
        if i < n - 1:
            v2 = ease((lt - it.get("at", 1 + i * 2) - 0.8) / 0.4); ax = x + bw + 10; ex = x + bw + gap - 10
            d.line([(ax, y + 100), (ax + (ex - ax) * v2, y + 100)], fill=alpha(GOLD, v2), width=4)
            if v2 > 0.95: d.polygon([(ex, y + 100), (ex - 18, y + 88), (ex - 18, y + 112)], fill=GOLD)
    for k, sp in enumerate(P.get("sparks", [])):
        v = ease((lt - sp.get("at", 0.5)) / 0.8); bx = 80 + k * 620; by = 660; random.seed(sp.get("seed", k))
        rr(d, [bx, by, bx + 560, by + 240], 12, alpha(PANEL2, v), outline=alpha(GRID2, v)); d.text((bx + 16, by + 12), sp["label"], font=F["h3"], fill=alpha(sp.get("col", GOLD), v))
        pts = []; yv = 0.3
        for j in range(40): yv = max(0.05, min(0.95, yv + random.gauss(sp.get("drift", 0.012), 0.03))); pts.append((bx + 20 + j * 13, by + 225 - yv * 170))
        nn = max(2, int(len(pts) * v)); d.line(pts[:nn], fill=alpha(sp.get("col", GOLD), v), width=4); g2.line(pts[:nn], fill=mix((0, 0, 0), sp.get("col", GOLD), 0.4), width=10)
    if P.get("footer"): big(d, g2, W / 2, 940, P["footer"], GOLD, ease((lt - P.get("footer_at", 9)) / 0.6), "h3", center=True)
    return pil

def tpl_cards(P, t, lt, s, canvas, d, g):
    """Numbered list reveal (plan / recap) with a small chart thumbnail."""
    img, gl, _ = draw_chart(760, 560, t, zoom=P.get("zoom", 0.0), level=True, level2=P.get("level2", False), labels=False, title=P.get("title", ""))
    frame = np.zeros((H, W, 3), np.uint8); frame = paste_np(frame, np.asarray(img), 80, 240)
    warped = camera(frame, t, tilt=0.22, drift=0.5); canvas = np.where(warped.sum(2, keepdims=True) > 20, warped, canvas)
    gframe = np.zeros((H, W, 3), np.uint8); gframe = paste_np(gframe, np.asarray(gl), 80, 240); canvas = glow_composite(canvas, camera(gframe, t, tilt=0.22, drift=0.5), 61)
    pil = Image.fromarray(canvas); d = ImageDraw.Draw(pil); g2 = ImageDraw.Draw(Image.new("RGB", (W, H), (0, 0, 0)))
    if P.get("headline"): big(d, g2, 90, 110, P["headline"], WHITE, ease(lt / 0.5), "h2")
    x0 = 920; yy = 180
    for i, it in enumerate(P.get("items", [])):
        v = ease((lt - it.get("at", 1 + i * 2.2)) / 0.5); col = it.get("col", WHITE); slide = (1 - v) * 80
        big(d, g2, x0 + slide, yy - 8, str(i + 1), GOLD, v, "h1")
        big(d, g2, x0 + 90 + slide, yy + 10, it["t"], col, v, "h3")
        if it.get("sub"): d.text((x0 + 90 + slide, yy + 54), it["sub"], font=F["body"], fill=alpha(MUTED, v))
        yy += P.get("row_h", 130)
    return pil

def tpl_outro(P, t, lt, s, canvas, d, g):
    pil = Image.fromarray(canvas); d = ImageDraw.Draw(pil); g2 = ImageDraw.Draw(Image.new("RGB", (W, H), (0, 0, 0)))
    v = ease(lt / 0.8); wolf(d, g2, W / 2, 300, 130, GOLD, v)
    big(d, g2, W / 2, 470, "ANONYMOUS WOLF TRADER", WHITE, v, "h1", center=True)
    d.rectangle([W / 2 - 240 * v, 565, W / 2 + 240 * v, 569], fill=GOLD)
    s1 = E("CTA", "SUBSCRIBE FOR THE NEXT GOLD UPDATE"); v2 = ease((lt - 0.8) / 0.6); pw = tw(d, s1, F["h3"]) / 2 + 40
    rr(d, [W / 2 - pw, 600, W / 2 + pw, 660], 30, alpha(GOLD, v2)); d.text((W / 2 - tw(d, s1, F["h3"]) / 2, 612), s1, font=F["h3"], fill=alpha((20, 16, 6), v2))
    for i, l in enumerate(["This is my own analysis and not financial advice.", "Trade your own plan. Manage your risk."]):
        d.text(((W - tw(d, l, F["body"])) / 2, 700 + i * 44), l, font=F["body"], fill=alpha(MUTED, ease((lt - 1.4 - i * 0.5) / 0.6)))
    return pil

TPL = {"hero_chart": tpl_hero_chart, "split": tpl_split, "impact": tpl_impact, "quote": tpl_quote, "timeline": tpl_timeline, "chain": tpl_chain, "cards": tpl_cards, "outro": tpl_outro}

# ---------- bumper (AI clip) ----------
BUMPER = None
if os.path.exists(E("BUMPER", "assets/ai_bumper.mp4")):
    cap = cv2.VideoCapture(E("BUMPER", "assets/ai_bumper.mp4")); frames = []
    while True:
        ok, fr = cap.read()
        if not ok: break
        frames.append(cv2.cvtColor(cv2.resize(fr, (W, H)), cv2.COLOR_BGR2RGB))
    if frames: BUMPER = frames
def bumper_frame(lt):
    if not BUMPER: return None
    i = int(lt * (len(BUMPER) / 8.0)) % len(BUMPER); return BUMPER[i].copy()

# ---------- transitions ----------
def transition(prev_img, cur_img, u, kind):
    if kind == "wipe":
        m = np.zeros((H, W, 1), np.float32); x = int(W * u); m[:, :x] = 1
        m = cv2.GaussianBlur(m, (0, 0), 25)[..., None] if x > 0 else m
        out = (prev_img * (1 - m) + cur_img * m)
        edge = np.exp(-((np.arange(W) - x) / 30.0) ** 2)[None, :, None] * 60 * np.array([1, .85, .45])
        return np.clip(out + edge, 0, 255).astype(np.uint8)
    if kind == "zoom":
        k = 1 + 0.12 * (1 - u); M = np.float32([[k, 0, W / 2 * (1 - k)], [0, k, H / 2 * (1 - k)]])
        z = cv2.warpAffine(cur_img, M, (W, H)); return (prev_img * (1 - u) + z * u).astype(np.uint8)
    return (prev_img * (1 - u) + cur_img * u).astype(np.uint8)

def render_scene(t, s):
    P = PLAN.get(s["para"], {"template": "hero_chart"}); lt = t - s["start"]
    if P["template"] == "bumper" and BUMPER:
        fr = bumper_frame(lt); fr = (fr * 0.9).astype(np.uint8)
        pil = Image.fromarray(fr); d = ImageDraw.Draw(pil); g2 = ImageDraw.Draw(Image.new("RGB", (W, H), (0, 0, 0)))
        if P.get("hook"):
            y = 600
            for i, l in enumerate(P["hook"].split("|")):
                v = ease((lt - 0.4 - i * 1.0) / 0.5); col = WHITE if i == 0 else GOLD; lw = tw(d, l, F["h1"])
                plate(d, [80, y - 10, 80 + lw + 50, y + 92], v * 0.9); d.rectangle([80, y - 10, 88, y + 92], fill=alpha(col, v)); big(d, g2, 110, y, l, col, v, "h1"); y += 112
        return np.asarray(pil)
    canvas = background(t, tint=P.get("tint"))
    pil = Image.fromarray(canvas); d = ImageDraw.Draw(pil); g = ImageDraw.Draw(Image.new("RGB", (W, H), (0, 0, 0)))
    if P["template"] == "bumper":
        P = dict(P, template="hero_chart", headline=P.get("hook", ""), zoom=0.6, level=True)
    tplname = P["template"] if P["template"] in TPL else "hero_chart"
    pil = TPL[tplname](P, t, lt, s, canvas, d, g)
    d = ImageDraw.Draw(pil); gl = Image.new("RGB", (W, H), (0, 0, 0)); g2 = ImageDraw.Draw(gl)
    if tplname != "outro": hud(d, g2, t, 1.0)
    if P.get("caption", True) and tplname not in ("quote", "outro", "impact"): caption(d, g2, t)
    out = glow_composite(pil, gl, 41, 0.9)
    return vignette(out, 0.22)

_PREV = {}
def render(t):
    s = scene_at(t); img = render_scene(t, s)
    # transition in from previous scene for the first 0.5 s
    idx = SC.index(s); lt = t - s["start"]
    if idx > 0 and lt < 0.5:
        if idx not in _PREV: _PREV[idx] = render_scene(s["start"] - 0.001, SC[idx - 1])
        prev = _PREV[idx]; kind = ["wipe", "zoom", "fade"][idx % 3]
        img = transition(prev.astype(np.float32), img.astype(np.float32), ease_io(lt / 0.5), kind)
    img[::4] = (img[::4].astype(np.int16) - 5).clip(0, 255).astype(np.uint8)
    gf = min(1.0, t / 0.8, max(0.0, (TOTAL - t) / 1.2))
    if gf < 1: img = (img * gf).astype(np.uint8)
    return img

if __name__ == "__main__":
    import subprocess
    f0, f1 = int(T0 * FPS), int(T1 * FPS)
    pr = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
    for f in range(f0, f1):
        pr.stdin.write(render(f / FPS).tobytes())
        if f % 150 == 0: print(f"frame {f}/{f1}", flush=True)
    pr.stdin.close(); pr.wait(); print("done", OUT)
