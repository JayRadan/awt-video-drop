#!/usr/bin/env python3
"""Build the final audio mix: voice (delayed) + music bed (ducked) + scene sound effects.
Usage: python3 sfx.py timing.json voice.mp3 [music.mp3|none] out.wav
Scene-local effect times mirror the animation moments in engine.py.
"""
import sys, json, math, subprocess
import numpy as np

SR = 48000
T = json.load(open(sys.argv[1]))
VOICE, MUSIC, OUT = sys.argv[2], sys.argv[3], sys.argv[4]
LEAD = 1.0
TOTAL = T["scenes"][-1]["end"] + 2.5
n_total = int(TOTAL * SR)

def load(path):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()

def env(n, a=0.005, d=0.1, s=0.0, r=0.1):
    t = np.arange(n) / SR
    e = np.ones(n) * s
    ia, idr = int(a * SR), int(d * SR)
    e[:ia] = np.linspace(0, 1, ia) if ia else 1
    e[ia:ia + idr] = np.linspace(1, s, min(idr, n - ia)) if idr else s
    ir = int(r * SR)
    if ir and ir < n:
        e[-ir:] *= np.linspace(1, 0, ir)
    return e

def lowpass(x, cutoff):
    # one-pole, cutoff may be array (per-sample) or scalar
    y = np.zeros_like(x); acc = 0.0
    if np.isscalar(cutoff):
        a = math.exp(-2 * math.pi * cutoff / SR)
        for i in range(len(x)):
            acc = a * acc + (1 - a) * x[i]; y[i] = acc
    else:
        al = np.exp(-2 * np.pi * cutoff / SR)
        for i in range(len(x)):
            acc = al[i] * acc + (1 - al[i]) * x[i]; y[i] = acc
    return y

rng = np.random.default_rng(3)
def whoosh(dur=0.6, down=False, gain=0.5):
    n = int(dur * SR); t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    sweep = np.linspace(600, 6000, n) if not down else np.linspace(5000, 300, n)
    x = lowpass(noise, sweep) * env(n, 0.05, 0.0, 1.0, dur * 0.7)
    return x / (np.abs(x).max() + 1e-9) * gain

def tick(freq=1800, dur=0.05, gain=0.25):
    n = int(dur * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * freq * t) * np.exp(-t * 60) * gain

def blip(freq=880, dur=0.18, gain=0.3):
    n = int(dur * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(2 * np.pi * freq * 2 * t)) * np.exp(-t * 18) * gain

def thud(gain=0.7):
    n = int(0.6 * SR); t = np.arange(n) / SR
    f = 110 * np.exp(-t * 6) + 45
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5)
    click = lowpass(rng.standard_normal(n), 1500) * np.exp(-t * 60) * 0.6
    return (x + click) * gain

def impact(gain=0.8):
    n = int(1.4 * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * 52 * t) * np.exp(-t * 2.2)
    boom = lowpass(rng.standard_normal(n), 300) * np.exp(-t * 4) * 0.8
    return (x + boom) * gain

def alert(gain=0.3):
    n = int(0.5 * SR); t = np.arange(n) / SR
    f = np.where(t < 0.12, 1320, np.where(t < 0.24, 0, 990))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-((t % 0.12)) * 25)
    return x * gain

def rise(dur=2.2, gain=0.45):
    n = int(dur * SR); t = np.arange(n) / SR
    x = lowpass(rng.standard_normal(n), np.linspace(200, 4000, n)) * (t / dur) ** 2
    tone = np.sin(2 * np.pi * np.cumsum(np.linspace(60, 240, n)) / SR) * (t / dur) * 0.6
    y = x + tone
    return y / (np.abs(y).max() + 1e-9) * gain

def chord(gain=0.35, dur=3.0):
    n = int(dur * SR); t = np.arange(n) / SR
    y = sum(np.sin(2 * np.pi * f * t) * (1 / (i + 1)) for i, f in enumerate([130.8, 196.0, 261.6, 329.6]))
    return y * env(n, 0.4, 0.0, 1.0, 1.8) * gain

def place(track, snd, at):
    i = int(at * SR)
    if i < 0 or i >= len(track): return
    m = min(len(snd), len(track) - i)
    track[i:i + m] += snd[:m]

sfx = np.zeros(n_total, dtype=np.float32)
scenes = T["scenes"]
S = {s["para"]: s for s in scenes}

# intro
place(sfx, rise(), 0.0)
place(sfx, blip(1200, gain=0.25), 0.9)
place(sfx, tick(2200, gain=0.2), 1.9)
# scene changes
for s in scenes[1:]:
    place(sfx, whoosh(0.55, gain=0.45), s["start"] - 0.15)
# range: candle draw ticks (first ~6s)
if 1 in S:
    st = S[1]["start"]
    for k in range(40):
        place(sfx, tick(1500 + (k % 3) * 200, dur=0.03, gain=0.06), st + 0.4 + k * 0.14)
    place(sfx, blip(660, gain=0.22), st + 6.1)
# players: three bars + big arrow
if 2 in S:
    st = S[2]["start"]
    for k in range(3): place(sfx, blip(520 - k * 60, gain=0.22), st + 0.9 + k * 0.6)
    place(sfx, thud(gain=0.45), st + 3.3)
# gamma: level draws in, then label locks
if 3 in S:
    st = S[3]["start"]
    place(sfx, whoosh(1.4, gain=0.25), st + 1.0)
    place(sfx, thud(gain=0.6), st + 2.6)
    place(sfx, alert(gain=0.22), st + 2.7)
# put-heavy: green up arrow
if 4 in S:
    st = S[4]["start"]
    place(sfx, rise(0.9, gain=0.3), st + 6.3)
    place(sfx, blip(990, gain=0.25), st + 7.2)
# rejection: zoom whoosh, three down ticks, absorbed thud
if 5 in S:
    st = S[5]["start"]
    place(sfx, whoosh(1.6, down=True, gain=0.3), st + 0.2)
    for k in range(3): place(sfx, blip(420 - k * 70, dur=0.25, gain=0.3), st + 2.6 + k * 0.45)
    place(sfx, thud(gain=0.5), st + 12.5)
# regime: tiles + impact
if 6 in S:
    st = S[6]["start"]
    for k in range(4): place(sfx, tick(900, dur=0.06, gain=0.18), st + 0.9 + k * 0.45)
    place(sfx, impact(gain=0.7), st + 6.0)
# summary: 1-2-3 ascending
if 7 in S:
    st = S[7]["start"]
    for k in range(3): place(sfx, blip(660 + k * 110, gain=0.28), st + 1.5 + k * 4.2)
# conclusion: breakdown
if 8 in S:
    st = S[8]["start"]
    place(sfx, whoosh(1.4, down=True, gain=0.4), st + 2.0)
    place(sfx, impact(gain=0.8), st + 3.4)
# outro
if 9 in S:
    place(sfx, chord(), S[9]["start"] + 0.2)
    place(sfx, blip(880, gain=0.2), S[9]["start"] + 0.8)

# voice
voice = load(VOICE)
vtrack = np.zeros(n_total, dtype=np.float32)
place(vtrack, voice, LEAD)

# music bed, looped, ducked under voice
mtrack = np.zeros(n_total, dtype=np.float32)
if MUSIC != "none":
    music = load(MUSIC)
    if len(music) > 0:
        reps = int(math.ceil(n_total / len(music))) + 1
        loop = np.tile(music, reps)[:n_total]
        # fade loop seams a bit and global in/out
        fade = int(1.5 * SR)
        loop[:fade] *= np.linspace(0, 1, fade); loop[-int(3 * SR):] *= np.linspace(1, 0, int(3 * SR))
        # ducking: envelope follower of voice
        win = int(0.05 * SR)
        venv = np.convolve(np.abs(vtrack), np.ones(win) / win, mode="same")
        venv = np.convolve(venv, np.ones(int(0.3 * SR)) / int(0.3 * SR), mode="same")
        gate = np.clip(venv / (venv.max() + 1e-9) * 6, 0, 1)
        duck = 1.0 - 0.6 * gate
        mtrack = loop * 0.16 * duck

mix = vtrack * 1.0 + mtrack + sfx * 0.9
peak = np.abs(mix).max()
if peak > 0.98: mix = mix / peak * 0.98
pcm = (mix * 32767).astype(np.int16)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-", OUT], input=pcm.tobytes(), check=True)
print("wrote", OUT, f"{TOTAL:.1f}s")
