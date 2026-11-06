import json, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import evchart as EC
W, H = 1080, 1920
FD = "/usr/share/fonts/opentype/inter/"
def f(sz, w="Black"): return ImageFont.truetype(FD + "InterDisplay-" + w + ".otf", sz)
data = EC.Data(json.load(open("candles_v.json"))["candles"], "2026-11-04T08:00")
GOLD = (242, 193, 78); RED = (255, 76, 76); GREEN = (46, 214, 160); WHITE = (245, 246, 250); CYAN = (90, 190, 255)
def chart_layer(view, box, items=(), dim=1.0, cx=0.62):
    img = Image.new("RGB", (W, H), (6, 8, 13))
    Ff = {"chart_title": f(1, "Bold"), "chart_meta": f(1, "Bold"), "axis": f(22, "SemiBold"), "axis_s": f(1, "Bold"), "label": f(26, "Bold")}
    spec = {"title": "", "instrument": " ", "view": [{"at": 0, "from": view[0], "to": view[1]}], "items": list(items), "asof_marker": False}
    EC.draw(img, box, spec, 99, data, Ff, 1.6)
    a = np.asarray(img).astype(np.float32) * dim
    yy, xx = np.mgrid[0:H, 0:W]; v = 1 - 0.55 * (((xx - W * cx) / W) ** 2 + ((yy - H * 0.5) / H) ** 2) * 2.2
    return Image.fromarray(np.clip(a * np.clip(v, 0.25, 1)[..., None], 0, 255).astype(np.uint8))
def text(d, xy, s, font, fill, stroke=6): d.text(xy, s, font=font, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))
def glow(img, color, box, r=80, k=0.6):
    g = Image.new("RGB", (W, H), (0, 0, 0)); ImageDraw.Draw(g).ellipse(box, fill=color); g = g.filter(ImageFilter.GaussianBlur(r))
    return Image.fromarray(np.clip(np.asarray(img).astype(np.int16) + (np.asarray(g) * k).astype(np.int16), 0, 255).astype(np.uint8))
im = chart_layer(("2026-11-03T00:00", "2026-11-06T09:00"), (40, 880, 1040, 1700), [{"type": "highlight", "from": "2026-11-06T03:00", "col": "green", "at": 0}], 0.95, 0.5)
im = glow(im, (90, 70, 10), (200, 900, 1000, 1500), 160, 0.5); d = ImageDraw.Draw(im)
text(d, (60, 150), "NFP TODAY", f(120), GOLD, 8)
text(d, (60, 300), "DOESN'T", f(150), WHITE, 9)
text(d, (60, 470), "MATTER.", f(150), WHITE, 9)
text(d, (60, 660), "BUY 4,040 → 4,250", f(90), GREEN, 7)
text(d, (60, 1760), "GOLD · 6 NOV · MY PLAN", f(52), WHITE, 5)
im.save("cover_9x16.jpg", quality=92); print("ok")
