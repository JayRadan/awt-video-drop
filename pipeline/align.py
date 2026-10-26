#!/usr/bin/env python3
"""Word-level alignment of the script to the voiceover (offline, pocketsphinx) -> timing.json with exact
sentence/scene times, plus words.json for per-word captions.
Usage: python3 align.py script.txt voice.mp3 lead_seconds [timing.json]
"""
import sys, re, json, subprocess, difflib
from pocketsphinx import Decoder, get_model_path
import os

script_path, voice, lead = sys.argv[1], sys.argv[2], float(sys.argv[3])
out = sys.argv[4] if len(sys.argv) > 4 else "timing.json"

# 1) decode whole file as one utterance
wav = "_align16k.wav"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", voice, "-ac", "1", "-ar", "16000", "-f", "wav", wav], check=True)
mp = get_model_path()
dec = Decoder(hmm=os.path.join(mp, "en-us", "en-us"), lm=os.path.join(mp, "en-us", "en-us.lm.bin"), dict=os.path.join(mp, "en-us", "cmudict-en-us.dict"), logfn="/dev/null")
raw = open(wav, "rb").read()[44:]
dec.start_utt()
for i in range(0, len(raw), 32000):
    dec.process_raw(raw[i:i + 32000], False, False)
dec.end_utt()
rec = [(s.word.split("(")[0].lower(), s.start_frame / 100.0, s.end_frame / 100.0) for s in dec.seg()
       if s.word not in ("<s>", "</s>", "<sil>", "[SPEECH]", "(NULL)") and not s.word.startswith("[")]
dur = len(raw) / 32000.0
print(f"recognized {len(rec)} words over {dur:.1f}s")

# 2) script tokens with sentence/paragraph ids
text = open(script_path).read().strip()
paras = [p.strip() for p in text.split("\n\n") if p.strip()]
NUM = {"0": "zero", "1": "one", "2": "two", "3": "three", "4": "four", "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine"}
def norm(w):
    w = w.lower().replace("’", "'")
    w = re.sub(r"[^a-z0-9']", "", w)
    return w
tokens = []  # (norm, sent_idx, para_idx)
sents = []
si = 0
for pi, p in enumerate(paras):
    for s in re.split(r"(?<=[.!?:])\s+", p):
        s = s.strip()
        if not s: continue
        sents.append({"text": s, "para": pi})
        for w in s.split():
            n = norm(w)
            if n: tokens.append((n, si, pi))
        si += 1

# 3) align with difflib on word sequences (numbers in script are digits; recognizer says words -> many mismatches,
#    but anchors on ordinary words are enough). Interpolate unmatched tokens between anchors.
a = [t[0] for t in tokens]; b = [r[0] for r in rec]
sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
tok_time = [None] * len(tokens)
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == "equal":
        for k in range(i2 - i1):
            tok_time[i1 + k] = (rec[j1 + k][1], rec[j1 + k][2])
matched = sum(1 for x in tok_time if x)
print(f"anchored {matched}/{len(tokens)} script words")
# interpolate
last_t = 0.0; idx = 0
while idx < len(tokens):
    if tok_time[idx] is None:
        j = idx
        while j < len(tokens) and tok_time[j] is None: j += 1
        t0 = tok_time[idx - 1][1] if idx > 0 else 0.0
        t1 = tok_time[j][0] if j < len(tokens) else dur
        n = j - idx
        for k in range(n):
            s0 = t0 + (t1 - t0) * k / n; s1 = t0 + (t1 - t0) * (k + 1) / n
            tok_time[idx + k] = (s0, s1)
        idx = j
    else:
        idx += 1
# enforce monotonic
for i in range(1, len(tok_time)):
    if tok_time[i][0] < tok_time[i - 1][1]:
        tok_time[i] = (tok_time[i - 1][1], max(tok_time[i][1], tok_time[i - 1][1] + 0.05))

# 3b) snap word edges to real speech: the recogniser folds pauses into the next word,
#     which makes captions run ahead after every pause. Trim leading/trailing silence.
import wave as _wave, numpy as _np
with _wave.open(wav) as _wf:
    _sr = _wf.getframerate(); _a = _np.frombuffer(_wf.readframes(_wf.getnframes()), _np.int16).astype(float)
_fr = _sr // 100; _e = _np.sqrt((_a[:len(_a) // _fr * _fr].reshape(-1, _fr) ** 2).mean(1))
_thr = _np.percentile(_e, 30) * 2.0; _sp = _e > _thr
for i, (s0, s1) in enumerate(tok_time):
    f0, f1 = int(s0 * 100), max(int(s0 * 100) + 1, int(s1 * 100))
    look = _sp[f0:f0 + 120]                      # first speech within 1.2 s of the claimed start
    if not look.any(): continue
    on = f0 + int(_np.argmax(look))
    if on - f0 >= 12:                            # >=120 ms of silence at the word start -> move it
        s0 = on / 100 - 0.03
        s1 = max(s1, s0 + 0.15)
        if i > 0 and tok_time[i - 1][1] > s0 - 0.02:  # previous word ran into the pause: trim it
            p0, p1 = tok_time[i - 1]; tok_time[i - 1] = (p0, max(p0 + 0.08, min(p1, s0 - 0.02)))
    if i + 1 < len(tok_time) and tok_time[i + 1][0] < s1:
        tok_time[i + 1] = (s1, max(tok_time[i + 1][1], s1 + 0.08))
    tok_time[i] = (s0, s1)
# trailing silence at the end of each word (so the highlight does not linger into pauses)
for i, (s0, s1) in enumerate(tok_time):
    f0, f1 = int(s0 * 100), int(s1 * 100)
    seg = _sp[f0:f1]
    if len(seg) and seg.any():
        off = f0 + len(seg) - int(_np.argmax(seg[::-1]))
        if f1 - off >= 15 and off / 100 + 0.05 - s0 >= 0.08: tok_time[i] = (s0, off / 100 + 0.05)

# 4) sentence + scene times
out_s = []
for si_, s in enumerate(sents):
    ts = [tok_time[i] for i, t in enumerate(tokens) if t[1] == si_]
    st, en = ts[0][0], ts[-1][1]
    out_s.append({"text": s["text"], "start": lead + st, "end": lead + en + 0.15, "para": s["para"]})
# make sentence ends touch next starts (no caption gaps)
for i in range(len(out_s) - 1):
    out_s[i]["end"] = max(out_s[i]["end"], out_s[i + 1]["start"] - 0.05) if out_s[i + 1]["start"] - out_s[i]["end"] < 0.6 else out_s[i]["end"]
scenes = []
for pi in range(len(paras)):
    ss = [x for x in out_s if x["para"] == pi]
    scenes.append({"para": pi, "start": ss[0]["start"], "end": ss[-1]["end"]})
for i in range(len(scenes) - 1): scenes[i]["end"] = scenes[i + 1]["start"]
scenes[0]["start"] = 0.0
scenes[-1]["end"] = lead + dur + 0.3
words = [{"w": orig, "start": lead + tok_time[i][0], "end": lead + tok_time[i][1], "sent": tokens[i][1]}
         for i, orig in enumerate([w for p in paras for s in re.split(r"(?<=[.!?:])\s+", p) if s.strip() for w in s.split() if norm(w)])]
json.dump({"sentences": out_s, "scenes": scenes, "words": words}, open(out, "w"), indent=1)
for sc in scenes: print(f"para {sc['para']}: {sc['start']:.1f} - {sc['end']:.1f}")
os.remove(wav)
