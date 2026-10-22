#!/usr/bin/env python3
"""Cut a vertical YouTube Short (1080x1920, <=58 s) from the finished long video. Zero credits.
Usage: python3 short.py timing.json final_long.mp4 out_short.mp4 [max_seconds]
Takes the hook (scene 0) + the first sentences of the key scene (the 'price action' paragraph 5 by default,
or the paragraph index in env SHORT_PARA) and the conclusion sentence, joined with short crossfades.
Layout: 9:16 canvas, dark background, the 16:9 frame scaled to full width in the middle,
title band on top ("GOLD · <date>"), caption band below, "full analysis on the channel" footer.
"""
import sys, os, json, subprocess, datetime
from PIL import Image, ImageDraw, ImageFont

T = json.load(open(sys.argv[1])); LONG = sys.argv[2]; OUT = sys.argv[3]
MAXS = float(sys.argv[4]) if len(sys.argv) > 4 else 56.0
KEY = int(os.environ.get("SHORT_PARA", "5"))
scenes = {s["para"]: s for s in T["scenes"]}
sents = T["sentences"]

def para_sents(p): return [x for x in sents if x["para"] == p]

# segments: hook (all of para 0), key para (as many sentences as fit), conclusion (first 2 sentences of para 8)
segs = []
h = scenes[0]; segs.append((h["start"], h["end"]))
budget = MAXS - (h["end"] - h["start"]) - 1.0
concl = para_sents(8)[:2]
c_len = concl[-1]["end"] - concl[0]["start"] if concl else 0
budget -= c_len
ks = para_sents(KEY); k0 = ks[0]["start"] if ks else None; k1 = k0
for x in ks:
    if x["end"] - k0 <= budget: k1 = x["end"]
    else: break
if k0 is not None and k1 > k0: segs.append((k0, k1))
if concl: segs.append((concl[0]["start"], concl[-1]["end"]))
total = sum(b - a for a, b in segs)
print("segments", [(round(a, 1), round(b, 1)) for a, b in segs], "total", round(total, 1))

# overlay (static PNG with alpha) for the 9:16 frame
W, H = 1080, 1920
FD = "/usr/share/fonts/opentype/inter/"
f_top = ImageFont.truetype(FD + "InterDisplay-ExtraBold.otf", 64)
f_sub = ImageFont.truetype(FD + "Inter-SemiBold.otf", 34)
f_foot = ImageFont.truetype(FD + "Inter-SemiBold.otf", 36)
ov = Image.new("RGBA", (W, H), (7, 10, 16, 255)); d = ImageDraw.Draw(ov)
for x in range(0, W, 64): d.line([(x, 0), (x, H)], fill=(12, 16, 25, 255))
for y in range(0, H, 64): d.line([(0, y), (W, y)], fill=(12, 16, 25, 255))
# video window transparent: 1080x608 centered at y=656
vy0 = (H - 608) // 2
d.rectangle([0, vy0, W, vy0 + 608], fill=(0, 0, 0, 0))
date = os.environ.get("SHORT_DATE", datetime.date.today().strftime("%d %b %Y").upper())
title = os.environ.get("SHORT_TITLE", "GOLD: WHO IS SELLING INTO 4,150?")
# wrap title
words = title.split(); lines = []; line = ""
for w_ in words:
    t_ = (line + " " + w_).strip()
    if d.textlength(t_, font=f_top) > W - 120 and line: lines.append(line); line = w_
    else: line = t_
if line: lines.append(line)
y = vy0 - 90 - 76 * len(lines)
for l in lines:
    d.text(((W - d.textlength(l, font=f_top)) / 2, y), l, font=f_top, fill=(236, 240, 248, 255)); y += 76
d.rectangle([W / 2 - 120, vy0 - 70, W / 2 + 120, vy0 - 64], fill=(242, 193, 78, 255))
d.text(((W - d.textlength("ANONYMOUS WOLF TRADER  ·  " + date, font=f_sub)) / 2, vy0 - 50), "ANONYMOUS WOLF TRADER  ·  " + date, font=f_sub, fill=(120, 132, 156, 255))
foot = "FULL ANALYSIS ON THE CHANNEL"
fw = d.textlength(foot, font=f_foot)
d.rounded_rectangle([(W - fw) / 2 - 36, vy0 + 608 + 420, (W + fw) / 2 + 36, vy0 + 608 + 490], radius=35, fill=(242, 193, 78, 255))
d.text(((W - fw) / 2, vy0 + 608 + 436), foot, font=f_foot, fill=(20, 16, 6, 255))
disc = "Not financial advice · my own analysis"
d.text(((W - d.textlength(disc, font=f_sub)) / 2, vy0 + 608 + 520), disc, font=f_sub, fill=(120, 132, 156, 255))
ov.save("short_overlay.png")

# captions: ASS file with segment-shifted times, rendered large under the video window
def ts(x):
    h = int(x // 3600); m = int(x % 3600 // 60); sec = x % 60
    return f"{h}:{m:02d}:{sec:05.2f}"
ass = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "", "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: Cap,Inter,54,&H00F8F0EC,&H00FFFFFF,&H00100A07,&H80000000,1,0,0,0,100,100,0,0,1,3,0,8,60,60," + str(vy0 + 608 + 40) + ",1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
offset = 0.0
for (a, b) in segs:
    for x in sents:
        s0, s1 = max(x["start"], a), min(x["end"], b)
        if s1 - s0 > 0.15:
            ass.append(f"Dialogue: 0,{ts(s0 - a + offset)},{ts(s1 - a + offset)},Cap,,0,0,0,,{x['text']}")
    offset += (b - a)
open("short_caps.ass", "w").write("\n".join(ass))

# build: cut each segment (re-encoded, scaled), concat, pad + overlay. Memory-light.
tmp = []
for i, (a, b) in enumerate(segs):
    fn = f"_seg{i}.mp4"; tmp.append(fn)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", LONG,
                    "-vf", "scale=1080:608,fade=t=in:st=0:d=0.25", "-af", f"afade=t=in:st=0:d=0.2,afade=t=out:st={max(0, b - a - 0.2):.3f}:d=0.2",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", fn], check=True)
open("_segs.txt", "w").write("".join(f"file '{f}'\n" for f in tmp))
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "_segs.txt", "-c", "copy", "_joined.mp4"], check=True)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "_joined.mp4", "-i", "short_overlay.png",
                "-filter_complex", f"[0:v]pad=1080:1920:0:{vy0}:color=#070a10[p];[p][1:v]overlay=0:0:format=auto,ass=short_caps.ass[outv]",
                "-map", "[outv]", "-map", "0:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
                "-c:a", "copy", "-movflags", "+faststart", OUT], check=True)
for f in tmp + ["_segs.txt", "_joined.mp4", "short_caps.ass"]:
    try: os.remove(f)
    except OSError: pass
print("wrote", OUT, "length", round(total, 1))
