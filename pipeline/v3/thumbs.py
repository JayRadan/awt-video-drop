import json, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import evchart as EC
W, H = 1280, 720
FD = "/usr/share/fonts/opentype/inter/"
def f(sz, w="Black"): return ImageFont.truetype(FD + "InterDisplay-" + w + ".otf", sz)
data = EC.Data(json.load(open("candles_v.json"))["candles"], "2026-11-06T09:00")
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
# A — NFP doesn't matter
im = chart_layer(("2026-11-03T00:00", "2026-11-06T09:00"), (520, 140, 1290, 710), [{"type": "highlight", "from": "2026-11-06T03:00", "col": "green", "at": 0}], 0.95)
im = glow(im, (90, 70, 10), (-200, -100, 600, 500), 140, 0.6); d = ImageDraw.Draw(im)
text(d, (48, 60), "NFP", f(190), GOLD, 9); text(d, (48, 270), "DOESN'T", f(110), WHITE); text(d, (48, 390), "MATTER.", f(110), WHITE)
text(d, (52, 560), "HERE'S WHY", f(64), GREEN, 5)
im.save("thumb_A.jpg", quality=92)
# B — stocks -4.4% gold -1.5%
im = Image.new("RGB", (W, H), (8, 10, 14)); d = ImageDraw.Draw(im)
text(d, (60, 70), "S&P 500", f(90), WHITE); text(d, (60, 170), "−4.4%", f(170), RED, 8)
text(d, (680, 70), "GOLD", f(90), WHITE); text(d, (680, 170), "−1.5%", f(170), GOLD, 8)
text(d, (60, 450), "THAT'S THE SIGNAL", f(90), GREEN, 6)
im.save("thumb_B.jpg", quality=92)
# C — buy 4040 target 4250
im = chart_layer(("2026-11-03T00:00", "2026-11-06T09:00"), (470, 140, 1290, 710), [{"type": "highlight", "from": "2026-11-06T03:00", "col": "green", "at": 0}], 0.95)
d = ImageDraw.Draw(im)
text(d, (48, 50), "BUYING", f(100), WHITE); text(d, (48, 160), "4,040", f(150), GREEN, 8)
text(d, (48, 360), "TARGET", f(100), WHITE); text(d, (48, 470), "4,250", f(150), GOLD, 8)
im.save("thumb_C.jpg", quality=92)
S = Image.new("RGB", (1920, 360), (30, 30, 30))
for i, k in enumerate("ABC"): S.paste(Image.open(f"thumb_{k}.jpg").resize((640, 360)), (i * 640, 0))
S.save("thumbs_sheet.png"); print("ok")
