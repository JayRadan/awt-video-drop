#!/usr/bin/env python3
"""AWT engine v3 — storyboard-driven financial-documentary renderer (16:9 long-form or native 9:16 trailer).
Usage: python3 engine3.py storyboard.json timing.json out.mp4 [start end]
 - storyboard.json: {"meta": {...}, "beats": [{"id", "sents": [i0, i1], "kind", "visual": {...}, "source_text", "sound": [...]}, ...]}
 - timing.json: align.py output (sentences, words). Beat times come from its sentences.
Visual templates: chart, headline, stat, compare, list, mechanism, scenarios, triggers, title, outro.
Every number on screen is either computed from the candle data (chart) or typed in the storyboard and checked by qa.py.
"""
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import evchart as EC

import sbutil
SB, T = sbutil.load(sys.argv[1], sys.argv[2]); OUT = sys.argv[3]
META = SB["meta"]; VERT = META.get("format") == "9x16"
W, H = (1080, 1920) if VERT else (1920, 1080); FPS = 30
S = 1.0 if not VERT else 1.0
SENTS = T["sentences"]; WORDS = T["words"]

# ---------- beats -> times ----------
BEATS = SB["beats"]
TOTAL = BEATS[-1]["end"]
T0 = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
T1 = float(sys.argv[5]) if len(sys.argv) > 5 else TOTAL

# ---------- style ----------
BG = (7, 9, 14); PANEL = (11, 14, 21); LINE = (30, 38, 56); GOLD = (242, 193, 78); RED = (255, 92, 92); GREEN = (46, 214, 160)
WHITE = (236, 239, 246); MUTED = (128, 138, 160); DIM = (78, 88, 108); CYAN = (90, 190, 255)
KIND = {"observation": ("EVIDENCE · WHAT HAPPENED", (90, 190, 255)), "interpretation": ("MY INTERPRETATION", GOLD),
        "scenario": ("SCENARIO · NOT PRICE ACTION", (190, 140, 255)), "plan": ("THE PLAN", GREEN), "context": ("CONTEXT", MUTED),
        "data": ("DATA · AS QUOTED", (90, 190, 255))}
FD = "/usr/share/fonts/opentype/inter/"
def font(sz, w="Bold", disp=True): return ImageFont.truetype(FD + ("InterDisplay-" if disp else "Inter-") + w + ".otf", int(sz))
k = 1.0 if not VERT else 1.12
kc = 1.0 if not VERT else 1.32
F = {"hero": font(150 * k, "ExtraBold"), "h1": font(84 * k, "ExtraBold"), "h2": font(54 * k, "Bold"), "h3": font(38 * k, "SemiBold"),
     "body": font(38 * k, "Medium", False), "sm": font(30 * k, "Medium", False), "item": font(46 * k, "Bold"), "tag": font(22 * k, "SemiBold", False),
     "cap": font(40 if not VERT else 64, "Bold" if VERT else "SemiBold", not VERT), "num": font(200 * k, "ExtraBold"),
     "chart_title": font(30 * kc, "Bold"), "chart_meta": font(19 * kc, "Medium", False), "axis": font(22 * kc, "Medium", False),
     "axis_s": font(18 * kc, "Medium", False), "label": font(22 * kc, "SemiBold", False), "src": font(19 * k, "Medium", False)}
def C(c): return EC.col(c)
def ease(x): return EC.ease(x)
def mix(a, b, u): u = max(0.0, min(1.0, u)); return tuple(int(a[i] + (b[i] - a[i]) * u) for i in range(3))
def fade(c, u): return mix(BG, C(c), u)
def tw(d, s, f): return d.textlength(s, font=f)
def wrap(d, s, f, maxw):
    out, line = [], ""
    for w in s.split():
        t = (line + " " + w).strip()
        if tw(d, t, f) > maxw and line: out.append(line); line = w
        else: line = t
    if line: out.append(line)
    return out

# ---------- data ----------
DATA = None
if META.get("candles"):
    DATA = EC.Data(json.load(open(META["candles"]))["candles"], META.get("asof"))

# ---------- background (calm, cached) ----------
yy, xx = np.mgrid[0:H, 0:W]
_r = np.sqrt(((xx - W * 0.5) / W) ** 2 + ((yy - H * 0.38) / H) ** 2)
_BG = np.clip(np.array([14, 18, 28], np.float32)[None, None, :] * np.clip(1.15 - _r * 1.4, 0.35, 1.0)[..., None], 0, 255).astype(np.uint8)
_rng = np.random.default_rng(1); _GRAIN = [(_rng.normal(0, 3.2, (H // 2, W // 2, 1))).astype(np.int8) for _ in range(6)]
_BGG = np.clip(_BG.astype(np.int16) + np.repeat(np.repeat(_GRAIN[0], 2, 0), 2, 1) // 2, 0, 255).astype(np.uint8)   # static grain: compresses well
def background(t):
    return _BGG.copy()

# ---------- layout ----------
M = 90 if not VERT else 64
TOP = 96 if not VERT else 210            # below HUD / title band
CAP_H = 150 if not VERT else 520         # caption zone at the bottom
CONTENT = (M, TOP + 54, W - M, H - CAP_H - 46)

def hud(d, t):
    if VERT:
        d.text((M, 70), META.get("brand", "ANONYMOUS WOLF TRADER"), font=F["tag"], fill=MUTED)
        d.text((M, 100), META.get("vdate", ""), font=F["tag"], fill=DIM)
        return
    d.rectangle([0, 0, W, 72], fill=(9, 11, 17)); d.line([(0, 72), (W, 72)], fill=LINE)
    d.text((M, 20), META.get("brand", "ANONYMOUS WOLF TRADER"), font=F["h3"].font_variant(size=30), fill=WHITE)
    d.text((M + 470, 28), META.get("vdate", ""), font=F["tag"], fill=MUTED)
    if DATA:
        c = DATA.c[-1]; s = f"PAXG-USD {c['c']:,.1f}  ·  AS OF {EC.datetime.datetime.fromtimestamp(DATA.asof, EC.datetime.timezone.utc).strftime('%d %b %H:%M UTC').upper()}"
        d.text((W - M - tw(d, s, F["tag"]), 28), s, font=F["tag"], fill=MUTED)

def kind_tag(d, b, u):
    kd = b.get("kind")
    if not kd or kd not in KIND: return
    lab, c = KIND[kd]; x, y = M, TOP if not VERT else 160
    w = tw(d, lab, F["tag"]) + 30
    d.rounded_rectangle([x, y, x + w, y + 38], radius=8, fill=fade(c, 0.14 * u), outline=fade(c, u), width=2)
    d.text((x + 15, y + 7), lab, font=F["tag"], fill=fade(c, u))

def source_line(d, b, u):
    s = b.get("source_text")
    if not s: return
    s = "SOURCE: " + s
    y = H - CAP_H - 34 if not VERT else H - CAP_H - 40
    for i, l in enumerate(wrap(d, s, F["src"], W - 2 * M)[:2][::-1]):
        d.text((M, y - i * 26), l, font=F["src"], fill=fade(DIM, u))

# ---------- captions ----------
def caption(d, t):
    if VERT: return caption_vert(d, t)
    cur = next((s for s in SENTS if s["start"] <= t < s["end"]), None)
    if not cur: return
    si = SENTS.index(cur); ws = [w for w in WORDS if w["sent"] == si]
    if not ws: return
    f = F["cap"]; lines, line = [], []
    for w in ws:
        if tw(d, " ".join(x["w"] for x in line + [w]), f) > 1400 and line: lines.append(line); line = [w]
        else: line.append(w)
    if line: lines.append(line)
    act = 0
    for li, l in enumerate(lines):
        if l[0]["start"] <= t: act = li
    first = min(act, max(0, len(lines) - 2)); show = lines[first:first + 2]
    lh = 52; y0 = H - 40 - lh * len(show)
    for li, l in enumerate(show):
        s = " ".join(x["w"] for x in l); x = (W - tw(d, s, f)) / 2; yy_ = y0 + li * lh
        for w in l:
            a = w["start"] <= t < w["end"] + 0.05; done = t >= w["end"]
            c = GOLD if a else (WHITE if done else (150, 158, 178))
            d.text((x + 2, yy_ + 2), w["w"], font=f, fill=(0, 0, 0)); d.text((x, yy_), w["w"], font=f, fill=c); x += tw(d, w["w"] + " ", f)

def caption_vert(d, t):
    i = next((k for k, w in enumerate(WORDS) if w["start"] <= t < (WORDS[k + 1]["start"] if k + 1 < len(WORDS) else w["end"] + 0.4)), None)
    if i is None: return
    s0 = i - (i % 3); ch = []
    for k_ in range(s0, min(len(WORDS), s0 + 3)):
        if ch and (WORDS[k_]["sent"] != ch[0]["sent"]): break
        ch.append(WORDS[k_])
    f = F["cap"]; s = " ".join(w["w"].upper() for w in ch)
    lines = wrap(d, s, f, W - 2 * M); y = H - CAP_H + 120
    for l in lines:
        x = (W - tw(d, l, f)) / 2
        for w in l.split():
            act = any(ww["w"].upper() == w and ww["start"] <= t < ww["end"] + 0.05 for ww in ch)
            for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3), (3, 3)): d.text((x + dx, y + dy), w, font=f, fill=(0, 0, 0))
            d.text((x, y), w, font=f, fill=GOLD if act else WHITE); x += tw(d, w + " ", f)
        y += 82

FLAGC = {"UNVERIFIED": (255, 176, 32), "CONTRADICTED": (255, 70, 70)}
def flag_badge(d, x, y, it, u):
    f = it.get("flag")
    if not f or u <= 0: return 0
    c = FLAGC.get(f, (255, 176, 32)); s = "⚠ " + f; w = tw(d, s, F["tag"]) + 24
    d.rounded_rectangle([x, y, x + w, y + 34], radius=6, fill=mix(BG, c, 0.25 * u), outline=fade(c, u), width=2)
    d.text((x + 12, y + 5), s, font=F["tag"], fill=fade(c, u)); return 42

# ---------- templates ----------
def T_chart(img, d, b, lt, dur):
    v = b["visual"]; x0, y0, x1, y1 = CONTENT
    if v.get("headline"):
        hl = v["headline"]; u = ease((lt - 0.2) / 0.5)
        lines = wrap(d, hl, F["h2"], x1 - x0)
        for i, l in enumerate(lines[:2]): d.text((x0, y0 + i * 62), l, font=F["h2"], fill=fade(WHITE, u))
        y0 += 62 * min(2, len(lines)) + 18
    EC.draw(img, (x0, y0, x1, y1), v, lt, DATA, F, S if not VERT else 1.0)

def T_headline(img, d, b, lt, dur):
    v = b["visual"]; x0, y0, x1, y1 = CONTENT
    if v.get("title"): d.text((x0, y0), v["title"], font=F["h3"], fill=fade(MUTED, ease(lt / 0.4))); y0 += 64
    items = v["items"]; n = len(items); gap = 24; h = (y1 - y0 - gap * (n - 1)) / n
    for i, it in enumerate(items):
        u = ease((lt - it.get("at", 0.3 + i * 1.2)) / 0.5)
        if u <= 0: continue
        yy_ = y0 + i * (h + gap) + (1 - u) * 30
        d.rounded_rectangle([x0, yy_, x1, yy_ + h], radius=14, fill=mix(BG, (16, 20, 30), u), outline=fade(LINE, u), width=2)
        d.rectangle([x0, yy_, x0 + 8, yy_ + h], fill=fade(GOLD, u))
        meta = f"{it['publisher'].upper()}  ·  {it['date'].upper()}"
        d.text((x0 + 36, yy_ + 22), meta, font=F["tag"], fill=fade(GOLD, u))
        f = F["h3"] if not VERT else F["h3"]
        for j, l in enumerate(wrap(d, "“" + it["headline"] + "”", f, x1 - x0 - 72)[:3]): d.text((x0 + 36, yy_ + 62 + j * 50), l, font=f, fill=fade(WHITE, u))
        d.text((x0 + 36, yy_ + h - 40), it.get("url_short", ""), font=F["src"], fill=fade(DIM, u))

def T_stat(img, d, b, lt, dur):
    v = b["visual"]; x0, y0, x1, y1 = CONTENT
    if v.get("title"): d.text((x0, y0), v["title"], font=F["h2"], fill=fade(WHITE, ease(lt / 0.4))); y0 += 90
    items = v["items"]; n = len(items)
    cols = n if not VERT else 1; rows = math.ceil(n / cols)
    cw = (x1 - x0) / cols; ch = (y1 - y0) / rows
    fv = F["num"] if n == 1 else F["hero"] if (n == 2 or VERT) else F["h1"].font_variant(size=int(116 * k))
    blk = 70 + fv.size * 1.1 + 3 * 36 + 50
    oy = max(0, (ch - blk) / 2) if rows == 1 else 0
    for i, it in enumerate(items):
        u = ease((lt - it.get("at", 0.3 + i * 0.8)) / 0.5)
        if u <= 0: continue
        cx = x0 + (i % cols) * cw; cy = y0 + (i // cols) * ch + oy
        c = C(it.get("col", "gold")); val = it["value"]
        if it.get("count"):
            a_, bb = it["count"]; val = it.get("fmt", "{:.1f}").format(a_ + (bb - a_) * ease((lt - it.get("at", 0.3)) / 1.4))
        ly = cy
        for l in wrap(d, it.get("label", "").upper(), F["tag"], cw - 40)[:2]: d.text((cx + 10, ly), l, font=F["tag"], fill=fade(MUTED, u)); ly += 30
        vf = fv
        while tw(d, val, vf) > cw - 30 and vf.size > 60: vf = vf.font_variant(size=int(vf.size * 0.9))
        d.text((cx + 6, ly + 8), val, font=vf, fill=fade(c, u))
        sy = ly + 8 + vf.size * 1.08
        sy += flag_badge(d, cx + 10, sy, it, u)
        for j, l in enumerate(wrap(d, it.get("sub", ""), F["sm"], cw - 40)[:3]): d.text((cx + 10, sy + j * 34), l, font=F["sm"], fill=fade(WHITE, u * 0.85))

def T_compare(img, d, b, lt, dur):
    v = b["visual"]; x0, y0, x1, y1 = CONTENT
    if v.get("title"): d.text((x0, y0), v["title"], font=F["h2"], fill=fade(WHITE, ease(lt / 0.4))); y0 += 86
    hl, hr = v.get("left_head", "WE SAID"), v.get("right_head", "WHAT HAPPENED")
    mid = x0 + (x1 - x0) * (0.5 if not VERT else 0.5)
    d.text((x0, y0), hl, font=F["tag"], fill=MUTED); d.text((mid + 20, y0), hr, font=F["tag"], fill=MUTED); y0 += 40
    rows = v["rows"]; rh = min(250 if not VERT else 300, (y1 - y0) / len(rows))
    for i, r in enumerate(rows):
        u = ease((lt - r.get("at", 0.4 + i)) / 0.5); u2 = ease((lt - r.get("at2", r.get("at", 0.4 + i) + 0.8)) / 0.5)
        yy_ = y0 + i * rh
        if u > 0:
            d.rounded_rectangle([x0, yy_, mid - 10, yy_ + rh - 16], radius=12, fill=mix(BG, (14, 18, 27), u), outline=fade(LINE, u), width=2)
            for j, l in enumerate(wrap(d, r["left"], F["h3"], mid - x0 - 50)[:3]): d.text((x0 + 22, yy_ + 18 + j * 46), l, font=F["h3"], fill=fade(WHITE, u))
        if u2 > 0:
            c = C(r.get("col", "green"))
            d.rounded_rectangle([mid + 10, yy_, x1, yy_ + rh - 16], radius=12, fill=mix(BG, tuple(int(v_ * 0.14) for v_ in c), u2), outline=fade(c, u2), width=2)
            for j, l in enumerate(wrap(d, r["right"], F["h3"], x1 - mid - 120)[:3]): d.text((mid + 32, yy_ + 18 + j * 46), l, font=F["h3"], fill=fade(WHITE, u2))
            m = r.get("mark", "✓"); d.text((x1 - 64, yy_ + 14), m, font=F["h2"], fill=fade(c, u2))

def T_list(img, d, b, lt, dur):
    v = b["visual"]; x0, y0, x1, y1 = CONTENT
    if v.get("title"): d.text((x0, y0), v["title"], font=F["h2"], fill=fade(WHITE, ease(lt / 0.4))); y0 += 90
    items = v["items"]; rh = min(190 if not VERT else 260, (y1 - y0) / len(items))
    for i, it in enumerate(items):
        u = ease((lt - it.get("at", 0.4 + i)) / 0.5)
        if u <= 0: continue
        yy_ = y0 + i * rh; c = C(it.get("col", "white"))
        d.text((x0, yy_ - 10), str(i + 1), font=F["h1"], fill=fade(GOLD, u))
        tl = wrap(d, it["t"], F["item"], x1 - x0 - 110)[:2]
        for j, l in enumerate(tl): d.text((x0 + 100, yy_ + j * 54), l, font=F["item"], fill=fade(c, u))
        for j, l in enumerate(wrap(d, it.get("sub", ""), F["sm"], x1 - x0 - 110)[:2]): d.text((x0 + 100, yy_ + 58 * len(tl) + j * 36), l, font=F["sm"], fill=fade(MUTED, u))

def T_mechanism(img, d, b, lt, dur):
    v = b["visual"]; x0, y0, x1, y1 = CONTENT
    if v.get("title"): d.text((x0, y0), v["title"], font=F["h2"], fill=fade(WHITE, ease(lt / 0.4))); y0 += 100
    items = v["items"]; n = len(items)
    if not VERT:
        gap = 70; bw = (x1 - x0 - gap * (n - 1)) / n; bh = 360; by = y0 + (y1 - y0 - bh) / 2 - 20
        boxes = [(x0 + i * (bw + gap), by, x0 + i * (bw + gap) + bw, by + bh) for i in range(n)]
    else:
        gap = 54; bh = min(210, (y1 - y0 - gap * (n - 1)) / n); boxes = [(x0, y0 + i * (bh + gap), x1, y0 + i * (bh + gap) + bh) for i in range(n)]
    for i, (it, bx) in enumerate(zip(items, boxes)):
        u = ease((lt - it.get("at", 0.4 + i * 1.2)) / 0.5)
        if u <= 0: continue
        c = C(it.get("col", "white"))
        d.rounded_rectangle(bx, radius=14, fill=mix(BG, (14, 18, 27), u), outline=fade(c, u), width=3)
        for j, l in enumerate(wrap(d, it["t"], F["item"], bx[2] - bx[0] - 40)[:3]): d.text((bx[0] + 22, bx[1] + 20 + j * 54), l, font=F["item"], fill=fade(c, u))
        for j, l in enumerate(wrap(d, it.get("sub", ""), F["sm"], bx[2] - bx[0] - 40)[:3]): d.text((bx[0] + 22, bx[3] - 118 + j * 36), l, font=F["sm"], fill=fade(MUTED, u))
        flag_badge(d, bx[0], bx[3] + 12, it, u)
        if i > 0:
            p = boxes[i - 1]
            if not VERT: a_, b_ = (p[2] + 10, (p[1] + p[3]) / 2), (bx[0] - 12, (bx[1] + bx[3]) / 2)
            else: a_, b_ = ((p[0] + p[2]) / 2, p[3] + 8), ((bx[0] + bx[2]) / 2, bx[1] - 10)
            e = (a_[0] + (b_[0] - a_[0]) * u, a_[1] + (b_[1] - a_[1]) * u); d.line([a_, e], fill=GOLD, width=4)
            if u > 0.95:
                if not VERT: d.polygon([(b_[0], b_[1]), (b_[0] - 16, b_[1] - 10), (b_[0] - 16, b_[1] + 10)], fill=GOLD)
                else: d.polygon([(b_[0], b_[1]), (b_[0] - 10, b_[1] - 16), (b_[0] + 10, b_[1] - 16)], fill=GOLD)
    if v.get("footer"):
        u = ease((lt - v.get("footer_at", 3)) / 0.5)
        if u > 0:
            f = F["h3"]; s = v["footer"]; d.text(((W - tw(d, s, f)) / 2, y1 - 54), s, font=f, fill=fade(GOLD, u))

def T_scenarios(img, d, b, lt, dur):
    v = b["visual"]; x0, y0, x1, y1 = CONTENT
    d.text((x0, y0), v.get("title", "MY SCENARIO ESTIMATES"), font=F["h2"], fill=fade(WHITE, ease(lt / 0.4)))
    d.text((x0, y0 + 66), v.get("subtitle", "My own probability estimates — not market prices."), font=F["sm"], fill=fade(MUTED, ease(lt / 0.4)))
    y0 += 120; rows = v["rows"]; rh = (y1 - y0) / len(rows)
    lab_w = 520 if not VERT else 0; bar_w = 300 if not VERT else (x1 - x0)
    for i, r in enumerate(rows):
        u = ease((lt - r.get("at", 0.4 + i * 0.8)) / 0.6)
        if u <= 0: continue
        yy_ = y0 + i * rh; c = C(r.get("col", "white")); act = r.get("focus") is None or (r.get("focus")[0] <= lt < r.get("focus")[1])
        dim = 1.0 if act else 0.45
        d.text((x0, yy_ + 4), f"{r['id']} · {r['name']}", font=F["item"], fill=fade(c, u * dim))
        if VERT: yb = yy_ + 54; xb = x0
        else: yb = yy_ + 12; xb = x0 + lab_w
        pw = bar_w * r["p"] * u
        d.rounded_rectangle([xb, yb, xb + bar_w, yb + 34], radius=8, fill=(16, 20, 30))
        d.rounded_rectangle([xb, yb, xb + max(8, pw), yb + 34], radius=8, fill=fade(c, 0.85 * dim))
        d.text((xb + bar_w + 16, yb - 6), f"~{round(r['p'] * 100)}%", font=F["item"], fill=fade(WHITE, u * dim))
        ox = (xb + bar_w + 200) if not VERT else x0; oy = yb if not VERT else yb + 50
        for j, l in enumerate(wrap(d, r["outcome"], F["sm"], (x1 - ox) if not VERT else (x1 - x0))[:2]): d.text((ox, oy + j * 36), l, font=F["sm"], fill=fade(WHITE, u * dim * 0.9))

def T_triggers(img, d, b, lt, dur):
    v = b["visual"]; x0, y0, x1, y1 = CONTENT
    d.text((x0, y0), v.get("title", "WHAT WOULD CHANGE MY MIND"), font=F["h2"], fill=fade(WHITE, ease(lt / 0.4))); y0 += 96
    cols = [("MORE CONFIDENT IF", v.get("more", []), GREEN), ("LESS CONFIDENT IF", v.get("less", []), RED)]
    inv_h = 120; area_b = y1 - inv_h - 20
    if not VERT:
        cw = (x1 - x0 - 40) / 2; boxes = [(x0, y0, x0 + cw, area_b), (x0 + cw + 40, y0, x1, area_b)]
    else:
        hh = (area_b - y0 - 30) / 2; boxes = [(x0, y0, x1, y0 + hh), (x0, y0 + hh + 30, x1, area_b)]
    for (head, its, c), bx in zip(cols, boxes):
        d.rounded_rectangle(bx, radius=14, fill=(12, 15, 23), outline=mix(BG, c, 0.5), width=2)
        d.text((bx[0] + 24, bx[1] + 18), head, font=F["tag"], fill=c); yy_ = bx[1] + 64
        for it in its:
            u = ease((lt - it.get("at", 0.5)) / 0.5)
            if u <= 0: continue
            for j, l in enumerate(wrap(d, "• " + it["t"], F["body"], bx[2] - bx[0] - 48)[:3]): d.text((bx[0] + 24, yy_ + j * 40), l, font=F["body"], fill=fade(WHITE, u));
            yy_ += 40 * min(3, len(wrap(d, "• " + it["t"], F["body"], bx[2] - bx[0] - 48))) + 18
    if v.get("invalidation"):
        u = ease((lt - v.get("inv_at", 1.0)) / 0.5)
        if u > 0:
            d.rounded_rectangle([x0, y1 - inv_h, x1, y1], radius=14, fill=mix(BG, (60, 14, 14), u), outline=fade(RED, u), width=3)
            d.text((x0 + 26, y1 - inv_h + 16), "INVALIDATION", font=F["tag"], fill=fade(RED, u))
            d.text((x0 + 26, y1 - inv_h + 50), v["invalidation"], font=F["h3"], fill=fade(WHITE, u))

def T_title(img, d, b, lt, dur):
    v = b["visual"]; x0, y0, x1, y1 = CONTENT
    lines = v["lines"]; f = F["h1"] if not VERT else F["h1"]
    total = sum(len(wrap(d, l["t"], f, x1 - x0)) for l in lines) * (f.size * 1.15)
    y = y0 + (y1 - y0 - total) / 2 - 20
    if v.get("kicker"): d.text((x0, y - 60), v["kicker"], font=F["tag"], fill=fade(MUTED, ease(lt / 0.4)))
    for i, l in enumerate(lines):
        u = ease((lt - l.get("at", 0.2 + i * 0.9)) / 0.5); c = C(l.get("col", "white"))
        for ln in wrap(d, l["t"], f, x1 - x0):
            if u > 0: d.text((x0, y + (1 - u) * 24), ln, font=f, fill=fade(c, u))
            y += f.size * 1.15

def T_outro(img, d, b, lt, dur):
    v = b["visual"]; u = ease(lt / 0.6)
    s = META.get("brand", "ANONYMOUS WOLF TRADER"); f = F["h1"]
    d.text(((W - tw(d, s, f)) / 2, H * 0.36), s, font=f, fill=fade(WHITE, u))
    d.rectangle([W / 2 - 220 * u, H * 0.36 + 112, W / 2 + 220 * u, H * 0.36 + 116], fill=GOLD)
    cta = v.get("cta", ""); u2 = ease((lt - 0.8) / 0.5)
    for j, l in enumerate(wrap(d, cta, F["h3"], W - 2 * M)): d.text(((W - tw(d, l, F["h3"])) / 2, H * 0.36 + 150 + j * 50), l, font=F["h3"], fill=fade(GOLD, u2))
    for j, l in enumerate(["This is my own analysis and not financial advice.", "Trade your own plan. Manage your risk."]):
        d.text(((W - tw(d, l, F["sm"])) / 2, H * 0.36 + 270 + j * 40), l, font=F["sm"], fill=fade(MUTED, ease((lt - 1.4) / 0.5)))

TPL = {"chart": T_chart, "headline": T_headline, "stat": T_stat, "compare": T_compare, "list": T_list, "mechanism": T_mechanism,
       "scenarios": T_scenarios, "triggers": T_triggers, "title": T_title, "outro": T_outro}

def beat_at(t):
    for b in BEATS:
        if b["start"] <= t < b["end"]: return b
    return BEATS[-1] if t >= BEATS[-1]["start"] else BEATS[0]

def render_beat(t, b):
    lt = t - b["start"]; dur = b["end"] - b["start"]
    img = Image.fromarray(background(t)); d = ImageDraw.Draw(img)
    tpl = b["visual"]["template"]
    TPL[tpl](img, d, b, lt, dur)
    d = ImageDraw.Draw(img)
    if tpl != "outro":
        hud(d, t); kind_tag(d, b, ease(lt / 0.4)); source_line(d, b, ease((lt - 0.3) / 0.5))
        if b.get("captions", True): caption(d, t)
    return np.asarray(img)

_PREV = {}
def render(t):
    b = beat_at(t); img = render_beat(t, b); i = BEATS.index(b); lt = t - b["start"]
    xf = b.get("transition_in", 0.35)
    if i > 0 and lt < xf:
        if i not in _PREV: _PREV[i] = render_beat(b["start"] - 0.001, BEATS[i - 1]).astype(np.float32)
        u = EC.ease_io(lt / xf); img = (_PREV[i] * (1 - u) + img.astype(np.float32) * u).astype(np.uint8)
    gf = min(1.0, t / 0.6, max(0.0, (TOTAL - t) / 1.0))
    if gf < 1: img = (img * gf).astype(np.uint8)
    return img

if __name__ == "__main__":
    import subprocess
    f0, f1 = int(T0 * FPS), int(round(T1 * FPS))
    tmp = OUT[:-4] + ".part.mp4"
    pr = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-tune", "animation", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for f in range(f0, f1):
        pr.stdin.write(render(f / FPS).tobytes())
        if f % 150 == 0: print(f"frame {f}/{f1}", flush=True)
    pr.stdin.close(); rc = pr.wait()
    if rc == 0: os.replace(tmp, OUT); print("done", OUT)
    else: print("ffmpeg failed", rc); sys.exit(rc)
