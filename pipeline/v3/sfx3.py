#!/usr/bin/env python3
"""Sound v3: storyboard-driven cues + two profiles, then loudness-normalised.
Usage: python3 sfx3.py storyboard.json timing.json voice.mp3 music.mp3|none out.wav [profile]
profile: documentary (long-form: restrained — soft beat changes, cues only where the storyboard asks)
         trailer     (shorts: risers into hits, bass impacts on reveals, brief silences)
Cues in storyboard beats: {"cue": "reveal"|"hit"|"riser_hit"|"silence"|"whoosh"|"outro", "at"/"at_sent"/"at_word", "dur"}.
Output: 48 kHz stereo WAV normalised to -14 LUFS integrated, true peak <= -1.5 dBTP (two-pass loudnorm).
"""
import sys, os, json, math, subprocess, tempfile
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sbutil

SB, T = sbutil.load(sys.argv[1], sys.argv[2]); VOICE, MUSIC, OUT = sys.argv[3], sys.argv[4], sys.argv[5]
PROFILE = sys.argv[6] if len(sys.argv) > 6 else SB["meta"].get("audio_profile", "documentary")
SR = 48000; LEAD = 1.0
BEATS = SB["beats"]; TOTAL = BEATS[-1]["end"]; N = int(TOTAL * SR) + SR
rng = np.random.default_rng(7)

def load(path):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()
def lp(x, c):
    y = np.empty_like(x); acc = 0.0; al = np.exp(-2 * np.pi * (c if not np.isscalar(c) else np.full(len(x), c)) / SR)
    for i in range(len(x)): acc = al[i] * acc + (1 - al[i]) * x[i]; y[i] = acc
    return y
def env(n, a, r):
    e = np.ones(n); ia, ir = int(a * SR), int(r * SR)
    if ia: e[:ia] = np.linspace(0, 1, ia)
    if ir and ir < n: e[-ir:] *= np.linspace(1, 0, ir)
    return e
def whoosh(dur=0.6, gain=0.4, down=False):
    n = int(dur * SR); x = lp(rng.standard_normal(n), np.linspace(400, 6500, n) if not down else np.linspace(6000, 300, n)) * env(n, 0.05, dur * 0.6)
    return x / (np.abs(x).max() + 1e-9) * gain
def soft_swish(dur=0.4, gain=0.05):            # dark, short air swish (no bright sweep)
    n = int(dur * SR); x = lp(rng.standard_normal(n), np.linspace(300, 1800, n)) * env(n, 0.12, dur * 0.7)
    return x / (np.abs(x).max() + 1e-9) * gain
def tick(f=2400, dur=0.03, gain=0.1): t = np.arange(int(dur * SR)) / SR; return np.sin(2 * np.pi * f * t) * np.exp(-t * 70) * gain
def pop(f=880, gain=0.2):
    t = np.arange(int(0.16 * SR)) / SR; b = (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * np.exp(-t * 22) * gain
    c = tick(3200, 0.012, gain * 0.7); b[:len(c)] += c; return b
def thud(gain=0.4):
    t = np.arange(int(0.6 * SR)) / SR; f = 110 * np.exp(-t * 6) + 45
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5) + lp(rng.standard_normal(len(t)), 1500) * np.exp(-t * 60) * 0.5) * gain
def boom(gain=0.8):
    t = np.arange(int(1.6 * SR)) / SR
    sub = np.sin(2 * np.pi * np.cumsum(65 * np.exp(-t * 2.5) + 32) / SR) * np.exp(-t * 2.2)
    body = lp(rng.standard_normal(len(t)), 260) * np.exp(-t * 4) * 0.9; return (sub + body) * gain
def riser(dur=1.4, gain=0.35):
    n = int(dur * SR); t = np.arange(n) / SR
    y = lp(rng.standard_normal(n), np.linspace(200, 5000, n)) * (t / dur) ** 2 + np.sin(2 * np.pi * np.cumsum(np.linspace(70, 280, n)) / SR) * (t / dur) * 0.5
    return y / (np.abs(y).max() + 1e-9) * gain
def chord(gain=0.3, dur=3.0):
    t = np.arange(int(dur * SR)) / SR; y = sum(np.sin(2 * np.pi * f * t) / (i + 1) for i, f in enumerate([130.8, 196.0, 261.6, 329.6]))
    return y * env(len(t), 0.4, 1.8) * gain
def place(tr, s, at):
    i = int(at * SR)
    if i < 0: s = s[-i:]; i = 0
    if i >= len(tr): return
    m = min(len(s), len(tr) - i); tr[i:i + m] += s[:m]

# ---- "computer" sound set (Jacob, 18 Nov 2026): typing clicks, digital blips, confirm beeps; no swooshes, no booms ----
def bandnoise(n, lo, hi): x = rng.standard_normal(n); return lp(x, hi) - lp(x, lo)
def key(gain=0.05):                      # one soft keyboard click
    n = int(0.018 * SR); t = np.arange(n) / SR
    c = bandnoise(n, 1800, 7000) * np.exp(-t * 380) + np.sin(2 * np.pi * 180 * t) * np.exp(-t * 300) * 0.4
    return c / (np.abs(c).max() + 1e-9) * gain
def typing(dur=0.5, gain=0.05):          # a short burst of typing
    out = np.zeros(int(dur * SR) + SR // 10); x = 0.0
    while x < dur: place(out, key(gain * rng.uniform(0.6, 1.0)), x); x += rng.uniform(0.045, 0.1)
    return out
def blip(f=1900, dur=0.035, gain=0.05):  # clean digital blip
    t = np.arange(int(dur * SR)) / SR; return np.sin(2 * np.pi * f * t) * env(len(t), 0.002, dur * 0.6) * gain
def blips(fs=(1600, 2400), gap=0.06, gain=0.05):
    out = np.zeros(int((gap * len(fs) + 0.1) * SR))
    for k, f in enumerate(fs): place(out, blip(f, 0.035, gain), k * gap)
    return out
def confirm(gain=0.08):                  # "data locked" two-tone beep
    return blips((1320, 1980), 0.07, gain)
sfx = np.zeros(N, np.float32); silences = []
P = {"documentary": dict(beat=0.025, reveal=0.04, hit=0.06, music=0.11),
     "trailer": dict(beat=0.04, reveal=0.06, hit=0.09, music=0.22),
     "energetic": dict(beat=0.03, reveal=0.05, hit=0.075, music=0.19)}[PROFILE]
for i, b in enumerate(BEATS):
    st = b["start"]
    if i > 0: place(sfx, blips((2200, 1700), 0.05, P["beat"]), st - 0.08)
    for c in b.get("sound", []):
        at = st + c.get("at", 0.0); cue = c["cue"]
        if cue == "reveal": place(sfx, typing(0.35, P["reveal"]), at - 0.05)
        elif cue == "hit": place(sfx, confirm(P["hit"]), at)
        elif cue == "riser_hit": d = min(c.get("dur", 0.8), 0.8); place(sfx, typing(d, P["reveal"]), at - d); place(sfx, confirm(P["hit"]), at)
        elif cue == "whoosh": place(sfx, blips((1800, 2400, 3000), 0.04, P["beat"]), at)
        elif cue == "silence": silences.append((at, at + c.get("dur", 0.6)))
        elif cue == "outro": place(sfx, chord(0.12), at); place(sfx, blips((1320, 1760, 2640), 0.09, P["hit"]), at + 0.6)
if PROFILE == "trailer": place(sfx, typing(0.3, P["reveal"]), 0.0); place(sfx, confirm(P["hit"]), 0.3)

voice = load(VOICE); vt = np.zeros(N, np.float32); place(vt, voice, LEAD)
mt = np.zeros(N, np.float32)
if MUSIC != "none" and os.path.exists(MUSIC):
    m = load(MUSIC)
    if len(m):
        loop = np.tile(m, int(math.ceil(N / len(m))) + 1)[:N]
        loop[:int(1.5 * SR)] *= np.linspace(0, 1, int(1.5 * SR)); loop[-int(3 * SR):] *= np.linspace(1, 0, int(3 * SR))
        w = int(0.05 * SR); ve = np.convolve(np.abs(vt), np.ones(w) / w, mode="same"); ve = np.convolve(ve, np.ones(int(0.4 * SR)) / int(0.4 * SR), mode="same")
        duck = 1.0 - (0.5 if PROFILE == "energetic" else 0.65) * np.clip(ve / (ve.max() + 1e-9) * 6, 0, 1)
        mt = loop * P["music"] * duck
for a, b_ in silences:                       # brief silence: music and sfx drop out, voice stays
    i0, i1 = int(a * SR), int(b_ * SR); fadeN = int(0.08 * SR)
    g = np.ones(N, np.float32); g[i0:i1] = 0
    g[max(0, i0 - fadeN):i0] = np.linspace(1, 0, min(fadeN, i0)); g[i1:i1 + fadeN] = np.linspace(0, 1, len(g[i1:i1 + fadeN]))
    mt *= g; sfx *= g
# effects never sit on top of the voice: duck all sfx hard while words are spoken (Jacob, 18 Nov 2026)
w2 = int(0.03 * SR); vs = np.convolve(np.abs(vt), np.ones(w2) / w2, mode="same")
vs = np.convolve(vs, np.ones(int(0.25 * SR)) / int(0.25 * SR), mode="same")
sfx = sfx * (1.0 - 0.6 * np.clip(vs / (np.percentile(vs[vs > 0], 60) + 1e-9), 0, 1))
mix = vt + mt + sfx
mix = mix / max(1.0, np.abs(mix).max() / 0.95)
tmp = tempfile.mktemp(suffix=".wav")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", tmp], input=mix.astype(np.float32).tobytes(), check=True)
# two-pass loudnorm to -14 LUFS / -1.5 dBTP
r = subprocess.run(["ffmpeg", "-hide_banner", "-i", tmp, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
js = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}"
      f":measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-af", af, "-ar", str(SR), "-ac", "2", OUT], check=True)
os.remove(tmp)
print("wrote", OUT, f"{TOTAL:.1f}s", PROFILE, "input LUFS", js["input_i"])
