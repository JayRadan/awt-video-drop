"""Render full-size frames at given beat ids (beat end - 0.8 s, when everything is revealed) or times; save contact sheet + individual PNGs.
Usage: python3 preview.py storyboard.json timing.json out_prefix [B01 B05 ... | t=12.5 ...]"""
import sys, os
sb, tm, pref = sys.argv[1:4]; sel = sys.argv[4:]
sys.argv = ["engine3.py", sb, tm, "/dev/null"]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "engine3.py")).read().split('if __name__ == "__main__":')[0]
g = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "engine3.py")}; exec(compile(src, "engine3", "exec"), g)
from PIL import Image
times = []
for s in sel:
    if s.startswith("t="): times.append((s, float(s[2:])))
    else:
        b = next(x for x in g["BEATS"] if x["id"] == s); times.append((s, max(b["start"] + 0.5, b["end"] - 0.8)))
ims = []
for name, t in times:
    im = Image.fromarray(g["render"](t)); im.save(f"{pref}_{name}.png"); ims.append(im)
w, h = ims[0].size; sc = 640 / w if w > h else 360 / w
th = [i.resize((int(w * sc), int(h * sc))) for i in ims]; cols = 2 if w > h else 4
rows = (len(th) + cols - 1) // cols; S = Image.new("RGB", (th[0].width * cols, th[0].height * rows))
for i, im in enumerate(th): S.paste(im, ((i % cols) * im.width, (i // cols) * im.height))
S.save(f"{pref}_sheet.png"); print("ok", [round(t, 1) for _, t in times])
