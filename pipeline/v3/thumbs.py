"""Three thumbnail concepts for the pilot, rendered from real candles + typography (no generated charts).
Each sells ONE tension the video fulfils. Output: thumb_A.jpg, thumb_B.jpg, thumb_C.jpg (1280x720)."""
import json, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import evchart as EC
W, H = 1280, 720
FD = "/usr/share/fonts/opentype/inter/"
def f(sz, w="Black"): return ImageFont.truetype(FD + "InterDisplay-" + w + ".otf", sz)
data = EC.Data(json.load(open("candles_pilot.json"))["candles"], "2026-10-28T10:00")
GOLD = (242, 193, 78); RED = (255, 76, 76); GREEN = (46, 214, 160); WHITE = (245, 246, 250)

def chart_layer(view, box, items=(), dim=1.0):
    img = Image.new("RGB", (W, H), (6, 8, 13))
    Ff = {"chart_title": f(1, "Bold"), "chart_meta": f(1, "Bold"), "axis": f(22, "SemiBold"), "axis_s": f(1, "Bold"), "label": f(24, "Bold")}
    spec = {"title": "", "instrument": " ", "view": [{"at": 0, "from": view[0], "to": view[1]}], "items": list(items), "asof_marker": False}
    EC.draw(img, box, spec, 99, data, Ff, 1.6)
    a = np.asarray(img).astype(np.float32) * dim
    yy, xx = np.mgrid[0:H, 0:W]; v = 1 - 0.55 * (((xx - W * 0.62) / W) ** 2 + ((yy - H * 0.5) / H) ** 2) * 2.2
    return Image.fromarray(np.clip(a * np.clip(v, 0.25, 1)[..., None], 0, 255).astype(np.uint8))

def text(d, xy, s, font, fill, stroke=6):
    d.text(xy, s, font=font, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))

def glow(img, color, box, r=60, k=0.55):
    g = Image.new("RGB", (W, H), (0, 0, 0)); ImageDraw.Draw(g).ellipse(box, fill=color)
    g = g.filter(ImageFilter.GaussianBlur(r)); return Image.fromarray(np.clip(np.asarray(img).astype(np.int16) + (np.asarray(g) * k).astype(np.int16), 0, 255).astype(np.uint8))

# A — the real danger: a dodge, not a hawk
im = chart_layer(("2026-10-25T00:00", "2026-10-29T10:00"), (600, 150, 1300, 710),
                 [{"type": "level", "price": 4100, "col": "red", "style": "solid", "at": 0},
                  {"type": "scenario", "path": [["asof", "close"], ["2026-10-29T06:00", 4112]], "col": "red", "at": 0, "draw": 0.01, "region_label": ""}], 0.95)
im = glow(im, (120, 20, 20), (700, 0, 1300, 360), 90, 0.6); d = ImageDraw.Draw(im)
text(d, (52, 70), "THE REAL", f(92), WHITE); text(d, (52, 170), "DANGER", f(150), RED)
text(d, (52, 350), "ISN'T A", f(70), WHITE); text(d, (52, 430), "HAWK.", f(120), GOLD)
d.rounded_rectangle([1030, 120, 1238, 172], radius=10, fill=RED); d.text((1046, 128), "EXIT 4,100", font=f(34, "ExtraBold"), fill=WHITE)
im.save("thumb_A.jpg", quality=92)

# B — A or B: which way tonight
im = chart_layer(("2026-10-26T00:00", "2026-10-29T12:00"), (40, 210, 1000, 710),
                 [{"type": "scenario", "path": [["asof", "close"], ["2026-10-29T08:00", 3975]], "col": "green", "at": 0, "draw": 0.01, "region_label": ""},
                  {"type": "scenario", "path": [["asof", "close"], ["2026-10-29T08:00", 4125]], "col": "red", "at": 0, "draw": 0.01, "region_label": ""}], 0.9)
d = ImageDraw.Draw(im)
text(d, (48, 36), "FED TONIGHT:", f(78), WHITE)
text(d, (48, 128), "WHICH WAY?", f(78), GOLD)
d.rounded_rectangle([1010, 160, 1240, 260], radius=14, fill=(110, 24, 24), outline=RED, width=4); d.text((1030, 172), "+2%?", font=f(70), fill=WHITE)
d.rounded_rectangle([990, 540, 1250, 640], radius=14, fill=(10, 80, 60), outline=GREEN, width=4); d.text((1006, 556), "−1.5%?", font=f(58), fill=WHITE)
im.save("thumb_B.jpg", quality=92)

# C — one number: my line in the sand
im = chart_layer(("2026-10-22T00:00", "2026-10-28T10:00"), (0, 260, 1280, 720),
                 [{"type": "level", "price": 4100, "col": "red", "style": "solid", "at": 0}], 0.7)
im = glow(im, (90, 70, 10), (380, -120, 1100, 360), 120, 0.7); d = ImageDraw.Draw(im)
text(d, (60, 40), "SHORT INTO THE FED", f(64), WHITE, 5)
text(d, (56, 112), "4,100", f(250), GOLD, 8)
text(d, (760, 190), "MY LINE", f(64), WHITE, 5); text(d, (760, 262), "IN THE SAND", f(54), RED, 5)
im.save("thumb_C.jpg", quality=92)
print("ok")
