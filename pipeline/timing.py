"""Build sentence + scene timing from the script and the voiceover pause map."""
import re, json

def load_silences(path):
    gaps = []
    cur = None
    for line in open(path):
        k, v = line.split()
        v = float(v)
        if k == "start":
            cur = v
        elif k == "end" and cur is not None:
            gaps.append(((cur + v) / 2, v - cur))
            cur = None
    return gaps

def build(script_path, sil_path, voice_len, lead):
    text = open(script_path).read().strip()
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    sents, para_of = [], []
    for pi, p in enumerate(paras):
        for s in re.split(r"(?<=[.!?:])\s+", p):
            s = s.strip()
            if s:
                sents.append(s)
                para_of.append(pi)
    total = sum(len(s) for s in sents)
    gaps = load_silences(sil_path)
    # proportional boundaries, snapped to nearest pause midpoint
    bounds = [0.0]
    acc = 0
    for s in sents[:-1]:
        acc += len(s)
        t = voice_len * acc / total
        best = min(gaps, key=lambda g: abs(g[0] - t)) if gaps else (t, 0)
        if abs(best[0] - t) < 1.6 and best[0] > bounds[-1] + 0.8:
            t = best[0]
        bounds.append(max(t, bounds[-1] + 0.5))
    bounds.append(voice_len)
    out = []
    for i, s in enumerate(sents):
        out.append({"text": s, "start": lead + bounds[i], "end": lead + bounds[i + 1], "para": para_of[i]})
    # scene = paragraph spans
    scenes = []
    for pi in range(len(paras)):
        ss = [x for x in out if x["para"] == pi]
        scenes.append({"para": pi, "start": ss[0]["start"], "end": ss[-1]["end"]})
    return out, scenes

if __name__ == "__main__":
    import sys
    sents, scenes = build(sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]))
    json.dump({"sentences": sents, "scenes": scenes}, open("timing.json", "w"), indent=1)
    for sc in scenes:
        print(f"para {sc['para']}: {sc['start']:.1f} - {sc['end']:.1f}")
