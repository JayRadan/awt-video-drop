"""Evidence chart: real OHLC candles drawn flat and fully labelled (instrument, timeframe, dates, units).
Overlays are animated by time: reveal, highlight, level, zone, measure (computed from the data), scenario
(projection drawn in a separate, hatched 'not price action' region), as-of marker.
All values shown are computed from the candle data or given explicitly by the storyboard.
"""
import math, datetime
from PIL import ImageDraw

UP = (40, 196, 150); DN = (226, 72, 72); AX = (96, 106, 128); GRIDC = (24, 30, 44); TXT = (200, 206, 220)
COLS = {"gold": (242, 193, 78), "red": (255, 92, 92), "green": (46, 214, 160), "white": (232, 236, 244), "muted": (125, 136, 160), "cyan": (90, 190, 255)}
def col(c): return COLS.get(c, c) if isinstance(c, str) else tuple(c)
def ease(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3
def ease_io(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
def ts(s): return datetime.datetime.strptime(s[:16], "%Y-%m-%dT%H:%M").replace(tzinfo=datetime.timezone.utc).timestamp()
def fmt(p): return f"{p:,.0f}" if abs(p) >= 1000 else f"{p:,.2f}"

class Data:
    def __init__(self, candles, asof=None):
        self.c = [dict(x, ts=ts(x["t"])) for x in candles]
        if asof: self.c = [x for x in self.c if x["ts"] <= ts(asof)]
        self.asof = self.c[-1]["ts"]
    def at(self, t):
        t = ts(t) if isinstance(t, str) else t
        best = min(self.c, key=lambda x: abs(x["ts"] - t)); return best
    def val(self, spec):
        """spec: {'t': '2026-10-23T20:00', 'f': 'c'|'o'|'h'|'l'} or {'p': price}; 'f': 'hi'/'lo' over range via 'from'/'to'"""
        if "p" in spec: return float(spec["p"]), (ts(spec["t"]) if "t" in spec else self.asof)
        if spec.get("f") in ("max", "min"):
            a, b = ts(spec["from"]), ts(spec["to"]); rng = [x for x in self.c if a <= x["ts"] <= b]
            x = max(rng, key=lambda k: k["h"]) if spec["f"] == "max" else min(rng, key=lambda k: k["l"])
            return (x["h"] if spec["f"] == "max" else x["l"]), x["ts"]
        x = self.at(spec["t"]); return x[spec.get("f", "c")], x["ts"]

def nice_step(span, n=5):
    raw = span / n; mag = 10 ** math.floor(math.log10(raw)); r = raw / mag
    return mag * (1 if r < 1.5 else 2 if r < 3 else 5 if r < 7 else 10)

def lerp(a, b, u): return a + (b - a) * u

def view_at(spec, lt, data):
    """view keyframes: [{'at':0,'from':..,'to':..}, {'at':3,'from':..,'to':..,'dur':1.6}, ...]; each later key eases in over [at, at+dur]."""
    keys = spec.get("view") or [{"at": 0, "from": data.c[max(0, len(data.c) - 120)]["t"], "to": data.c[-1]["t"]}]
    a, b = ts(keys[0]["from"]), ts(keys[0]["to"])
    for k in keys[1:]:
        if lt <= k["at"]: break
        u = ease_io((lt - k["at"]) / k.get("dur", 1.6)); a, b = lerp(a, ts(k["from"]), u), lerp(b, ts(k["to"]), u)
    return a, b

def draw(img, box, spec, lt, data, F, S=1.0):
    """img: PIL RGB; box: (x0,y0,x1,y1); spec: storyboard chart spec; lt: local time in beat; F: fonts dict."""
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    hdr = int(F["chart_title"].size + F["chart_meta"].size + 30 * S); pad_r = int(118 * S); pad_b = int(44 * S)
    px0, py0, px1, py1 = x0 + int(14 * S), y0 + hdr, x1 - pad_r, y1 - pad_b
    d.rounded_rectangle(box, radius=int(14 * S), fill=(9, 12, 19), outline=(30, 38, 56), width=max(1, int(2 * S)))
    # header: instrument / timeframe / units (always visible)
    inst = spec.get("instrument", "PAXG-USD · COINBASE · 1H CANDLES · USD PER TROY OZ · SPOT-GOLD PROXY · TIMES UTC")
    d.text((x0 + int(18 * S), y0 + int(12 * S)), spec.get("title", "GOLD"), font=F["chart_title"], fill=(236, 239, 246))
    if d.textlength(inst, font=F["chart_meta"]) > (x1 - x0) - int(150 * S):
        inst = spec.get("instrument_short", "PAXG-USD · 1H · USD/OZ · SPOT-GOLD PROXY · UTC")
    d.text((x0 + int(18 * S), y0 + int(18 * S) + F["chart_title"].size), inst, font=F["chart_meta"], fill=AX)
    BOUNDS[0], BOUNDS[1] = x0 + int(8 * S), x1 - int(8 * S)
    va, vb = view_at(spec, lt, data)
    # reveal
    rv = spec.get("reveal")
    vis_end = data.asof
    if rv:
        r0, r1 = ts(rv.get("from", data.c[0]["t"])), ts(rv.get("until", data.c[-1]["t"]))
        vis_end = lerp(r0, r1, ease_io((lt - rv.get("at", 0)) / rv.get("dur", 2.0)))
    cs = [c for c in data.c if va - 3600 <= c["ts"] <= vb and c["ts"] <= vis_end + 1]
    items = [it for it in spec.get("items", []) if lt >= it.get("at", 0)]
    lo = min([c["l"] for c in cs] or [data.c[-1]["l"]]); hi = max([c["h"] for c in cs] or [data.c[-1]["h"]])
    for it in spec.get("items", []):           # keep the y-range stable: include all planned overlays from the start
        for p in _prices(it, data): lo, hi = min(lo, p), max(hi, p)
    if spec.get("yrange"): lo, hi = spec["yrange"]
    span = max(hi - lo, 10); lo -= span * 0.08; hi += span * 0.10
    def X(t): return px0 + (t - va) / max(1, vb - va) * (px1 - px0)
    def Y(p): return py1 - (p - lo) / (hi - lo) * (py1 - py0)
    # grid + price axis
    st = nice_step(hi - lo, 5 if S >= 0.9 else 4); p = math.ceil(lo / st) * st
    while p <= hi:
        y = Y(p); d.line([(px0, y), (px1, y)], fill=GRIDC, width=1)
        d.text((px1 + int(12 * S), y - int(12 * S)), fmt(p), font=F["axis"], fill=AX); p += st
    d.text((px1 + int(12 * S), py0 - int(30 * S)), "USD/oz", font=F["axis_s"], fill=AX)
    # date axis: day boundaries (UTC)
    day = datetime.datetime.fromtimestamp(va, datetime.timezone.utc).replace(hour=0, minute=0) + datetime.timedelta(days=1)
    ndays = (vb - va) / 86400; dayw = (px1 - px0) / max(0.5, ndays); labw = d.textlength("MON 26 OCT", font=F["axis_s"]) + 16
    every = max(1, math.ceil(labw / max(1, dayw)))
    k = 0
    while day.timestamp() < vb:
        x = X(day.timestamp())
        d.line([(x, py0), (x, py1)], fill=(18, 23, 34), width=1)
        if k % every == 0:
            lab = day.strftime("%a %d %b").upper(); d.text((x + int(6 * S), py1 + int(10 * S)), lab, font=F["axis_s"], fill=AX)
        day += datetime.timedelta(days=1); k += 1
    # scenario region (future) shading first, so candles sit on top
    for it in items:
        if it["type"] == "scenario": _scenario_region(d, it, lt, data, X, Y, px0, py0, px1, py1, F, S)
    # candles
    n = max(1, (vb - va) / 3600); cw = max(1.0, (px1 - px0) / n * 0.62)
    for c in cs:
        x = X(c["ts"]); colr = UP if c["c"] >= c["o"] else DN
        d.line([(x, Y(c["h"])), (x, Y(c["l"]))], fill=colr, width=max(1, int(cw / 5)))
        yo, yc = Y(c["o"]), Y(c["c"]); d.rectangle([x - cw / 2, min(yo, yc), x + cw / 2, max(max(yo, yc), min(yo, yc) + 1)], fill=colr)
    # overlays
    for it in items:
        u = ease((lt - it.get("at", 0)) / it.get("dur", 0.6))
        getattr(_O, it["type"])(d, it, u, lt, data, X, Y, px0, py0, px1, py1, F, S)
    # last price tag / as-of marker
    if spec.get("asof_marker", True) and cs and cs[-1]["ts"] >= data.asof - 1:
        c = cs[-1]; y = Y(c["c"]); lab = fmt(c["c"]) if c["c"] < 1000 else f"{c['c']:,.1f}"
        tw_ = d.textlength(lab, font=F["axis"]); d.rounded_rectangle([px1 + int(6 * S), y - int(16 * S), px1 + int(14 * S) + tw_ + int(8 * S), y + int(16 * S)], radius=int(6 * S), fill=(242, 193, 78))
        d.text((px1 + int(14 * S), y - int(13 * S)), lab, font=F["axis"], fill=(14, 12, 6))
    return (X, Y)

def _prices(it, data):
    t = it["type"]
    if t == "level": return [it["price"]]
    if t == "zone": return [it["p1"], it["p2"]]
    if t == "measure": return [data.val(it["a"])[0], data.val(it["b"])[0]]
    if t == "scenario": return [data.c[-1]["c"] if p == "close" else p for _, p in it["path"]]
    if t == "highlight":
        a, b = ts(it["from"]), ts(it.get("to", it["from"])); r = [x for x in data.c if a <= x["ts"] <= b]
        return [min(x["l"] for x in r), max(x["h"] for x in r)] if r else []
    return []

BOUNDS = [0, 99999]
def _label(d, x, y, text, c, F, S, anchor="l", bg=(9, 12, 19)):
    f = F["label"]; w = d.textlength(text, font=f); h = int(30 * S)
    xx = x if anchor == "l" else x - w - int(16 * S)
    xx = max(BOUNDS[0], min(xx, BOUNDS[1] - w - int(16 * S)))
    d.rounded_rectangle([xx, y - h / 2, xx + w + int(16 * S), y + h / 2], radius=int(6 * S), fill=bg, outline=c, width=max(1, int(2 * S)))
    d.text((xx + int(8 * S), y - h / 2 + int(4 * S)), text, font=f, fill=c)

def _dash(d, a, b, c, w, on=12, off=8):
    (xa, ya), (xb, yb) = a, b; L = math.hypot(xb - xa, yb - ya)
    if L < 1: return
    n = int(L / (on + off)) + 1
    for i in range(n):
        s, e = i * (on + off) / L, min(1, (i * (on + off) + on) / L)
        d.line([(xa + (xb - xa) * s, ya + (yb - ya) * s), (xa + (xb - xa) * e, ya + (yb - ya) * e)], fill=c, width=w)

def _scenario_region(d, it, lt, data, X, Y, px0, py0, px1, py1, F, S):
    u = ease((lt - it.get("at", 0)) / 0.6)
    if u <= 0: return
    xa = max(px0, X(data.asof))
    if xa >= px1: return
    shade = tuple(int(9 + (24 - 9) * u * 0.6) for _ in range(3))
    d.rectangle([xa, py0, px1, py1], fill=(shade[0], shade[1], shade[2] + 6))
    step = int(26 * S)
    for k in range(-int((py1 - py0) / step), int((px1 - xa) / step) + 2):
        xs = xa + k * step; d.line([(xs, py1), (xs + (py1 - py0), py0)], fill=(20, 24, 36), width=1)
    d.line([(xa, py0), (xa, py1)], fill=(150, 160, 185), width=max(1, int(2 * S)))
    lab = it.get("region_label", "SCENARIO · MY VIEW · NOT PRICE ACTION")
    if lab == "": return
    room = px1 + int(100 * S) - xa - int(16 * S); yl = py0 + int(8 * S)
    lines = [lab] if d.textlength(lab, font=F["label"]) <= room else ["SCENARIO · MY VIEW", "NOT PRICE ACTION"]
    for ln in lines: d.text((xa + int(10 * S), yl), ln, font=F["label"], fill=(170, 178, 200)); yl += int(28 * S)
    asof = datetime.datetime.fromtimestamp(data.asof, datetime.timezone.utc).strftime("AS OF %d %b %H:%M UTC").upper()
    d.text((xa - d.textlength(asof, font=F["axis_s"]) - int(8 * S), py0 + int(8 * S)), asof, font=F["axis_s"], fill=(150, 160, 185))

class _O:
    @staticmethod
    def level(d, it, u, lt, data, X, Y, px0, py0, px1, py1, F, S):
        c = col(it.get("col", "gold")); y = Y(it["price"]); xe = px0 + (px1 - px0) * u
        if it.get("style", "dash") == "dash": _dash(d, (px0, y), (xe, y), c, max(2, int(3 * S)))
        else: d.line([(px0, y), (xe, y)], fill=c, width=max(2, int(3 * S)))
        if u > 0.6 and it.get("label"): _label(d, px0 + int(10 * S), y - int(22 * S), it["label"], c, F, S)
    @staticmethod
    def zone(d, it, u, lt, data, X, Y, px0, py0, px1, py1, F, S):
        c = col(it.get("col", "gold")); ya, yb = Y(it["p1"]), Y(it["p2"])
        xa = max(px0, X(data.asof)) if it.get("future") else px0
        fill = tuple(int(9 + (v - 9) * 0.16 * u) for v in c)
        d.rectangle([xa, min(ya, yb), px1, max(ya, yb)], fill=fill)
        d.line([(xa, ya), (px1, ya)], fill=tuple(int(v * 0.6) for v in c), width=1); d.line([(xa, yb), (px1, yb)], fill=tuple(int(v * 0.6) for v in c), width=1)
        if u > 0.5 and it.get("label"):
            ly = (max(ya, yb) - int(22 * S)) if it.get("future") else (min(ya, yb) - int(20 * S))
            _label(d, xa + int(10 * S), ly, it["label"], c, F, S)
    @staticmethod
    def highlight(d, it, u, lt, data, X, Y, px0, py0, px1, py1, F, S):
        c = col(it.get("col", "gold")); a, b = ts(it["from"]), ts(it.get("to", it["from"]))
        r = [x for x in data.c if a <= x["ts"] <= b]
        if not r: return
        lo, hi = min(x["l"] for x in r), max(x["h"] for x in r); pad = int(10 * S)
        xa, xb = X(a) - pad, X(b) + pad; ya, yb = Y(hi) - pad, Y(lo) + pad
        pulse = 0.5 + 0.5 * math.sin(lt * 5)
        w = max(2, int((3 + 2 * pulse * (1 - min(1, (lt - it.get('at', 0)) / 2))) * S))
        d.rounded_rectangle([xa, ya, xb, yb], radius=int(8 * S), outline=c, width=w)
        if it.get("label") and u > 0.5:
            above = it.get("label_pos", "above") == "above"
            _label(d, xa, (ya - int(22 * S)) if above else (yb + int(22 * S)), it["label"], c, F, S)
    @staticmethod
    def measure(d, it, u, lt, data, X, Y, px0, py0, px1, py1, F, S):
        c = col(it.get("col", "white")); pa, ta = data.val(it["a"]); pb, tb = data.val(it["b"])
        xa, ya, xb, yb = X(ta), Y(pa), X(tb), Y(pb); yb_u = ya + (yb - ya) * u
        _dash(d, (xa, ya), (xb + int(30 * S), ya), (150, 160, 185), max(1, int(2 * S)), 8, 6)
        xm = xb + int(30 * S); d.line([(xm, ya), (xm, yb_u)], fill=c, width=max(2, int(3 * S)))
        ah = int(12 * S); sgn = 1 if yb > ya else -1
        if u > 0.95: d.polygon([(xm - ah, yb - sgn * ah * 1.4), (xm + ah, yb - sgn * ah * 1.4), (xm, yb)], fill=c)
        if u > 0.9:
            dv = pb - pa; pct = dv / pa * 100
            lab = it.get("label") or f"{'+' if dv >= 0 else '−'}${abs(dv):,.0f}  ({'+' if dv >= 0 else '−'}{abs(pct):.1f}%)"
            _label(d, xm + int(12 * S), (ya + yb) / 2, lab, c, F, S)
    @staticmethod
    def scenario(d, it, u, lt, data, X, Y, px0, py0, px1, py1, F, S):
        c = col(it.get("col", "cyan")); pts = [(X(data.asof if p0 == "asof" else ts(p0)), Y(data.c[-1]["c"] if p == "close" else p)) for p0, p in it["path"]]
        uu = ease_io((lt - it.get("at", 0) - 0.4) / it.get("draw", 1.6))
        if uu <= 0: return
        L = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]; tot = sum(L) * uu; acc = 0
        last = pts[0]
        for i, l in enumerate(L):
            if acc + l <= tot: _dash(d, pts[i], pts[i + 1], c, max(3, int(4 * S)), 14, 9); last = pts[i + 1]; acc += l
            else:
                f = (tot - acc) / l; e = (pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f)
                _dash(d, pts[i], e, c, max(3, int(4 * S)), 14, 9); last = e; break
        r = int(8 * S); d.ellipse([last[0] - r, last[1] - r, last[0] + r, last[1] + r], outline=c, width=max(2, int(3 * S)))
        if uu > 0.95 and it.get("label"): _label(d, last[0] - int(12 * S), last[1] + int(30 * S) * (1 if it.get("label_below", True) else -1), it["label"], c, F, S, anchor="r")
    @staticmethod
    def note(d, it, u, lt, data, X, Y, px0, py0, px1, py1, F, S):
        c = col(it.get("col", "muted")); _label(d, px0 + int(10 * S), py1 - int(26 * S), it["text"], c, F, S)
