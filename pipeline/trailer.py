#!/usr/bin/env python3
"""Channel trailer renderer: reuses engine.py's drawing kit with its own 5-scene script.
Usage: LEVEL=4132 python3 trailer.py timing.json out.mp4
Scenes (paragraph order): 0 hook, 1 three lenses, 2 method/proof, 3 cadence, 4 close.
"""
import sys, os, json, subprocess
sys.argv_backup = list(sys.argv)
timing_path, OUT_FILE = sys.argv[1], sys.argv[2]
sys.argv = ["engine.py", timing_path, "/dev/null"]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "engine.py")).read().split("def main():")[0]
exec(src)

LENS_SPLIT = None  # computed from sentences in paragraph 1

def trailer_render(t):
    base = background(); d = ImageDraw.Draw(base)
    glow = Image.new("RGB", (W, H), (0, 0, 0)); g = ImageDraw.Draw(glow)
    d._image = base
    s = scene_at(t); p = s["para"]; lt = t - s["start"]; u = ease(lt / 0.5)
    dur = s["end"] - s["start"]

    if p == 0:  # hook over live chart
        topbar(d, g, t, u); ticker(d, t, u)
        chart(d, g, (40, 110, 1880, 870), t, frac=ease(lt / 2.5), level=False, crosshair=False, title="GOLD · 1H")
        veil = Image.new("RGB", (W, H), (0, 0, 0)); base.paste(Image.blend(base, veil, 0.4 * ease(lt / 0.4))); d = ImageDraw.Draw(base); d._image = base
        lines = [("MOST ANALYSIS TELLS YOU WHAT PRICE DID.", WHITE, 0.3), ("I TELL YOU WHO'S DOING IT.", GOLD, 2.2)]
        y = 560
        for line, col, at in lines:
            v = ease((lt - at) / 0.5); lw = tw(d, line, F["h1"])
            rr(d, [80, y - 10, 80 + lw + 50, y + 92], 8, alpha((6, 8, 14), v * 0.9)); d.rectangle([80, y - 10, 88, y + 92], fill=alpha(col, v))
            big_label(d, g, 110, y, line, col, v, "h1"); y += 112
    elif p == 1:  # three lenses, thirds of the scene
        topbar(d, g, t, u); ticker(d, t, u)
        # switch lenses on the sentences "Who is positioned", "Where option dealers", "And what the macro"
        sents = [x for x in T["sentences"] if x["para"] == 1]
        marks = [x["start"] for x in sents if x["text"].startswith(("Who is", "Where option", "And what"))]
        while len(marks) < 3: marks.append(s["start"] + dur * len(marks) / 3)
        k = max(0, sum(1 for m in marks if t >= m) - 1); lk = t - marks[k]
        chart(d, g, CHART_BOX, t, title="GOLD · 1H", level=(k >= 1), level_u=1.0 if k >= 1 else 0, wall=(k >= 1))
        if k == 0:
            positioning_panel(d, g, SIDE_BOX, t, ease(lk / 1.5)); big_label(d, g, 70, 150, "1 · WHO IS POSITIONED WHERE", WHITE, ease(lk / 0.5), "h2")
        elif k == 1:
            gamma_panel(d, g, SIDE_BOX, t, ease(lk / 1.5), highlight=True); big_label(d, g, 70, 150, "2 · WHERE DEALERS MUST HEDGE", WHITE, ease(lk / 0.5), "h2")
        else:
            macro_panel(d, g, SIDE_BOX, t, ease(lk / 1.5)); big_label(d, g, 70, 150, "3 · WHAT THE REGIME IS DOING", WHITE, ease(lk / 0.5), "h2")
        # progress dots
        for i in range(3):
            d.ellipse([W / 2 - 40 + i * 36, H - 200, W / 2 - 24 + i * 36, H - 184], fill=GOLD if i <= k else GRID2)
    elif p == 2:  # method / proof
        topbar(d, g, t, u); ticker(d, t, u)
        chart(d, g, CHART_BOX, t, title="GOLD · 1H · ONE LEVEL, ONE DIRECTION", level=True, level_u=ease(lt / 1.2), zoom_u=1.0, wall=True,
              rejections=lt > 2.5, breakdown=ease((lt - 4.5) / 1.5))
        x0, y0, x1, y1 = SIDE_BOX; rr(d, SIDE_BOX, 10, PANEL, outline=GRID2)
        d.text((x0 + 20, y0 + 16), "WHAT YOU GET", font=F["tag"], fill=MUTED)
        rows = [("ONE LEVEL", 0.8), ("ONE DIRECTION", 2.6), ("THE STRUCTURE BEHIND IT", 4.4)]
        for i, (a, at) in enumerate(rows):
            v = ease((lt - at) / 0.5); yy = y0 + 70 + i * 120
            rr(d, [x0 + 20, yy, x1 - 20, yy + 92], 8, alpha(PANEL2, v), outline=alpha(GOLD, v * 0.6))
            big_label(d, g, x0 + 40, yy + 22, a, GOLD if i < 2 else WHITE, v, "h3")
        nos = [("NO HYPE", 6.5), ("NO FACE", 7.3), ("NO SIGNALS SERVICE", 8.1)]
        for i, (a, at) in enumerate(nos):
            v = ease((lt - at) / 0.4); yy = y0 + 460 + i * 60
            d.text((x0 + 40, yy), "✕  " + a, font=F["h3"], fill=alpha(RED, v))
        v = ease((lt - 9.5) / 0.5)
        d.text((x0 + 40, y1 - 70), "JUST THE ANALYSIS.", font=F["h3"], fill=alpha(GOLD, v))
    elif p == 3:  # cadence
        topbar(d, g, t, u); ticker(d, t, u)
        chart(d, g, (40, 110, 1880, 870), t, title="GOLD · 1H", level=True, crosshair=False)
        veil = Image.new("RGB", (W, H), (0, 0, 0)); base.paste(Image.blend(base, veil, 0.5)); d = ImageDraw.Draw(base); d._image = base
        v = ease(lt / 0.6)
        big_label(d, g, W / 2 - tw(d, "3×", F["num"]) / 2 - 300, 300, "3×", GOLD, v, "num")
        big_label(d, g, W / 2 - 150, 330, "A WEEK", WHITE, v, "h1")
        v2 = ease((lt - 1.2) / 0.6)
        big_label(d, g, W / 2 - tw(d, "UNDER 7 MINUTES", F["h1"]) / 2, 480, "UNDER 7 MINUTES", WHITE, v2, "h1")
        d.text((W / 2 - tw(d, "positioning · option gamma · macro regime", F["h3"]) / 2, 600), "positioning · option gamma · macro regime", font=F["h3"], fill=alpha(MUTED, ease((lt - 1.8) / 0.6)))
    else:  # close
        v = ease(lt / 0.8)
        wolf_mark(d, g, W / 2, 300, 130, GOLD, v)
        big_label(d, g, W / 2 - tw(d, "ANONYMOUS WOLF TRADER", F["h1"]) / 2, 470, "ANONYMOUS WOLF TRADER", WHITE, v)
        d.rectangle([W / 2 - 240 * v, 565, W / 2 + 240 * v, 569], fill=GOLD)
        s1 = "SUBSCRIBE IF YOU TRADE GOLD WITH YOUR HEAD"
        v2 = ease((lt - 1.0) / 0.6); pw_ = tw(d, s1, F["h3"]) / 2 + 40
        rr(d, [W / 2 - pw_, 600, W / 2 + pw_, 660], 30, alpha(GOLD, v2))
        d.text((W / 2 - tw(d, s1, F["h3"]) / 2, 612), s1, font=F["h3"], fill=alpha((20, 16, 6), v2))
        s2 = "Not financial advice. My own analysis. Trade your own plan."
        d.text((W / 2 - tw(d, s2, F["body"]) / 2, 700), s2, font=F["body"], fill=alpha(MUTED, ease((lt - 1.6) / 0.6)))
        ticker(d, t, v)
    caption(d, g, t) if p in (0, 1, 2) else None
    out = composite(base, glow, 1.0, 41)
    out[::4] = (out[::4].astype(np.int16) - 6).clip(0, 255).astype(np.uint8)
    gf = min(1.0, t / 0.6, max(0.0, (TOTAL - t) / 1.2))
    if gf < 1: out = (out * gf).astype(np.uint8)
    return out

if __name__ == "__main__":
    nframes = int(TOTAL * FPS)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", OUT_FILE]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(nframes):
        pr.stdin.write(trailer_render(f / FPS).tobytes())
        if f % 150 == 0: print(f"frame {f}/{nframes}", flush=True)
    pr.stdin.close(); pr.wait(); print("done", OUT_FILE)
