#!/usr/bin/env python3
"""Sound design v2: cues derived from the scene plan + word timings. Zero credits.
Usage: SCENES=plan python3 sfx2.py timing.json voice.mp3 music.mp3|none out.wav
"""
import sys, os, json, math, subprocess, importlib.util, random
import numpy as np

SR = 48000
T = json.load(open(sys.argv[1])); VOICE, MUSIC, OUT = sys.argv[2], sys.argv[3], sys.argv[4]
LEAD = 1.0; TOTAL = T["scenes"][-1]["end"] + 2.0; n_total = int(TOTAL * SR)
spec = importlib.util.spec_from_file_location("plan", os.environ.get("SCENES", "plan") + ".py"); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
PLAN = {s["para"]: s for s in m.PLAN}
rng = np.random.default_rng(7); random.seed(7)

def load(path):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()
def lowpass(x, cutoff):
    y = np.empty_like(x); acc = 0.0
    al = np.exp(-2 * np.pi * (cutoff if not np.isscalar(cutoff) else np.full(len(x), cutoff)) / SR)
    for i in range(len(x)): acc = al[i] * acc + (1 - al[i]) * x[i]; y[i] = acc
    return y
def env(n, a, r):
    e = np.ones(n); ia, ir = int(a * SR), int(r * SR)
    if ia: e[:ia] = np.linspace(0, 1, ia)
    if ir and ir < n: e[-ir:] *= np.linspace(1, 0, ir)
    return e
def whoosh(dur=0.6, down=False, gain=0.45):
    n = int(dur * SR); noise = rng.standard_normal(n)
    sweep = np.linspace(500, 7000, n) if not down else np.linspace(6000, 250, n)
    x = lowpass(noise, sweep) * env(n, 0.05, dur * 0.6); return x / (np.abs(x).max() + 1e-9) * gain
def tick(f=1800, dur=0.05, gain=0.2):
    t = np.arange(int(dur * SR)) / SR; return np.sin(2 * np.pi * f * t) * np.exp(-t * 60) * gain
def blip(f=880, dur=0.2, gain=0.28):
    t = np.arange(int(dur * SR)) / SR; return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)) * np.exp(-t * 18) * gain
def thud(gain=0.6):
    t = np.arange(int(0.6 * SR)) / SR; f = 110 * np.exp(-t * 6) + 45
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5); c = lowpass(rng.standard_normal(len(t)), 1500) * np.exp(-t * 60) * 0.6
    return (x + c) * gain
def impact(gain=0.8):
    t = np.arange(int(1.4 * SR)) / SR; x = np.sin(2 * np.pi * 52 * t) * np.exp(-t * 2.2)
    boom = lowpass(rng.standard_normal(len(t)), 300) * np.exp(-t * 4) * 0.8; return (x + boom) * gain
def riser(dur=1.6, gain=0.4):
    n = int(dur * SR); t = np.arange(n) / SR
    x = lowpass(rng.standard_normal(n), np.linspace(200, 4000, n)) * (t / dur) ** 2
    tone = np.sin(2 * np.pi * np.cumsum(np.linspace(60, 240, n)) / SR) * (t / dur) * 0.6
    y = x + tone; return y / (np.abs(y).max() + 1e-9) * gain
def shimmer(gain=0.18, dur=1.2):
    t = np.arange(int(dur * SR)) / SR
    y = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * (3 + i)) for i, f in enumerate([1760, 2217, 2637, 3520])); return y * gain / 4
def chord(gain=0.35, dur=3.0):
    t = np.arange(int(dur * SR)) / SR
    y = sum(np.sin(2 * np.pi * f * t) * (1 / (i + 1)) for i, f in enumerate([130.8, 196.0, 261.6, 329.6])); return y * env(len(t), 0.4, 1.8) * gain
def data_ticks(dur, n, gain=0.05):
    out = np.zeros(int(dur * SR) + SR)
    for k in range(n):
        at = int(k * dur / n * SR); s = tick(1400 + rng.integers(0, 600), 0.03, gain); out[at:at + len(s)] += s
    return out

def place(track, snd, at):
    i = int(at * SR)
    if i < 0 or i >= len(track): return
    mlen = min(len(snd), len(track) - i); track[i:i + mlen] += snd[:mlen]

sfx = np.zeros(n_total, dtype=np.float32)
scenes = T["scenes"]
for idx, s in enumerate(scenes):
    P = PLAN.get(s["para"], {"template": "hero_chart"}); tpl = P["template"]; st = s["start"]
    # transition sound (matches engine: wipe / zoom / fade by index % 3)
    if idx > 0:
        kind = ["wipe", "zoom", "fade"][idx % 3]
        if kind == "wipe": place(sfx, whoosh(0.5, gain=0.42), st - 0.1)
        elif kind == "zoom": place(sfx, riser(0.7, gain=0.3), st - 0.6); place(sfx, thud(gain=0.4), st)
        else: place(sfx, whoosh(0.8, down=True, gain=0.25), st - 0.2)
    if tpl in ("bumper",) or (idx == 0):
        place(sfx, riser(2.0, gain=0.45), 0.0); place(sfx, thud(0.5), 2.0)
        for k in range(2): place(sfx, blip(1100 + k * 200, gain=0.22), 0.5 + k * 1.0)
    if tpl == "hero_chart":
        place(sfx, data_ticks(min(4.0, s["end"] - st), 24), st + 0.3)
        if P.get("level", True): place(sfx, thud(0.45), st + 1.2)
        for e in P.get("entries", []): place(sfx, blip(720, gain=0.25), st + e[3])
        if P.get("break_at"): place(sfx, whoosh(1.4, down=True, gain=0.4), st + P["break_at"]); place(sfx, impact(0.6), st + P["break_at"] + 1.2)
    if tpl == "impact":
        place(sfx, impact(0.8), st + 0.1); place(sfx, shimmer(), st + 0.3)
    if tpl == "quote":
        hot = set(w.upper() for w in P.get("hot", []))
        for w in T.get("words", []):
            if s["start"] <= w["start"] < s["end"] and (w["w"].strip(",.").upper() in hot or any(ch.isdigit() for ch in w["w"])):
                place(sfx, tick(2200, 0.04, 0.16), w["start"])
    if tpl == "timeline":
        for k in range(12): place(sfx, tick(900 + k * 40, 0.05, 0.12), st + 0.5 + k * 0.12)
        for co in P.get("callouts", []): place(sfx, blip(760 if co.get("col") != (255, 77, 77) else 420, gain=0.24), st + co["at"])
    if tpl == "chain":
        for it in P.get("items", []): place(sfx, blip(660 + 60 * P["items"].index(it), gain=0.26), st + it.get("at", 1))
        for sp in P.get("sparks", []): place(sfx, data_ticks(2.0, 14, 0.04), st + sp.get("at", 0.5))
    if tpl == "split":
        for r in P.get("rows", []): place(sfx, blip(520 if r.get("col") == (255, 77, 77) else 760, gain=0.22), st + r.get("at", 1))
        if P.get("footer"): place(sfx, thud(0.4), st + P.get("footer_at", 8))
    if tpl == "cards":
        for i, it in enumerate(P.get("items", [])): place(sfx, blip(600 + i * 90, gain=0.26), st + it.get("at", 1 + i * 2))
    if tpl == "outro":
        place(sfx, chord(), st + 0.2); place(sfx, blip(880, gain=0.2), st + 0.9)

voice = load(VOICE); vtrack = np.zeros(n_total, dtype=np.float32); place(vtrack, voice, LEAD)
mtrack = np.zeros(n_total, dtype=np.float32)
if MUSIC != "none" and os.path.exists(MUSIC):
    music = load(MUSIC)
    if len(music):
        loop = np.tile(music, int(math.ceil(n_total / len(music))) + 1)[:n_total]
        loop[:int(1.5 * SR)] *= np.linspace(0, 1, int(1.5 * SR)); loop[-int(3 * SR):] *= np.linspace(1, 0, int(3 * SR))
        win = int(0.05 * SR); venv = np.convolve(np.abs(vtrack), np.ones(win) / win, mode="same")
        venv = np.convolve(venv, np.ones(int(0.3 * SR)) / int(0.3 * SR), mode="same")
        duck = 1.0 - 0.6 * np.clip(venv / (venv.max() + 1e-9) * 6, 0, 1)
        mtrack = loop * 0.15 * duck
mixd = vtrack + mtrack + sfx * 0.9
peak = np.abs(mixd).max()
if peak > 0.98: mixd = mixd / peak * 0.98
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-", OUT], input=(mixd * 32767).astype(np.int16).tobytes(), check=True)
print("wrote", OUT, f"{TOTAL:.1f}s")
