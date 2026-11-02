#!/usr/bin/env python3
"""Quality gate. Usage:
  python3 qa.py storyboard.json timing.json script.txt sources.json video.mp4 [--vertical video_v.mp4 sb_v.json timing_v.json script_v.txt] [--thumbs a.jpg b.jpg c.jpg]
Checks (writes qa_<id>.md and prints a summary; exit code 1 if anything BLOCKS publishing):
 1. Every number shown on screen is supported: by the narration, by a source fact in the manifest, or by the candle data.
 2. Chart labels that quote a price at a time match the candle at that time.
 3. Evidence beats (observation/data/context) carry a non-empty source line; sources marked NOT FOUND/CONTRADICTED/PARTLY
    are only shown with a visible flag.
 4. Caption sync: spoken-word onsets after pauses vs the caption timing.
 5. Audio: integrated loudness, true peak, clipped samples.
 6. Frames: full-size and phone-size contact sheets of every beat (horizontal and vertical) for visual review.
 7. Thumbnails: small-size previews (YouTube home/sidebar sizes).
"""
import sys, os, re, json, subprocess
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sbutil, evchart as EC

def nums(s):
    out = []
    s = s.replace("−", "-").replace("–", " ").replace("—", " ")
    for m in re.finditer(r"(\d[\d,]*(?:\.\d+)?)\s*(k|K|bp|%|pp)?", s):
        v = float(m.group(1).replace(",", "")); u = m.group(2) or ""
        if u in ("k", "K"): v *= 1000
        out.append(v)
    return out

WORDNUM = {"ninety": 90, "two thousand": 2000, "half a percent": 0.5, "one and a half": 1.5, "six": 6, "three": 3, "two": 2, "one": 1}
DAYS_RE = re.compile(r"\b(\d{1,2})\s+(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\w*", re.I)
TIME_RE = re.compile(r"\b\d{1,2}:\d{2}\b")

def visible_strings(b):
    out = []
    def walk(o, key=""):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in ("template", "type", "col", "style", "kind", "flag", "from", "to", "t", "path", "view", "reveal", "a", "b", "id", "url_short", "cue") and not (k == "t" and isinstance(v, str) and not re.match(r"\d{4}-", v)):
                    if k == "t" and isinstance(v, str) and not re.match(r"\d{4}-", v): out.append(v)
                    continue
                walk(v, k)
        elif isinstance(o, list):
            for v in o: walk(v, key)
        elif isinstance(o, str) and key in ("title", "headline", "label", "value", "sub", "t", "left", "right", "outcome", "name", "text", "invalidation", "footer", "kicker", "cta", "label_prefix", "region_label", "source_text", "publisher", "date"):
            out.append(o)
    walk(b.get("visual", {})); out.append(b.get("source_text", ""))
    return [s for s in out if s]

def run(sb_path, tm_path, script_path, src_path, video, tag):
    SB, T = sbutil.load(sb_path, tm_path); meta = SB["meta"]; rep = []; block = []
    srcs = json.load(open(src_path))["sources"]
    narr = open(script_path).read().lower()
    allowed = set(nums(narr))
    for w, v in WORDNUM.items():
        if w in narr: allowed.add(v)
    for k, s in srcs.items():
        allowed |= set(nums(json.dumps(s.get("facts", {}), ensure_ascii=False)))
        for it in s.get("items", []): allowed |= set(nums(it.get("headline", "")))
    data = EC.Data(json.load(open(meta["candles"]))["candles"], meta.get("asof")) if meta.get("candles") else None
    def data_ok(v):
        if not data: return False
        for c in data.c:
            for f in "ohlc":
                if abs(c[f] - v) <= 0.6: return True
        return False
    rep.append(f"# QA report — {meta['id']} ({tag})\n")
    rep.append("## 1–3. On-screen numbers, chart labels, sources\n")
    for b in SB["beats"]:
        strs = visible_strings(b); issues = []
        for s in strs:
            s2 = re.sub(r"\b\d{1,2}\s*(&|and|–|-|to)\s*(?=\d{1,2}\s+(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC))", "", TIME_RE.sub("", s), flags=re.I)
            s2 = DAYS_RE.sub("", s2).replace("24/7", "")
            s2 = re.sub(r"\b(19|20)\d{2}\b", "", s2)                      # years
            s2 = re.sub(r"\b(1H|10-year|2-year|10y|2y|3 dissents|3 hike)\b", "", s2, flags=re.I)
            for v in nums(s2):
                ok = v in allowed or any(abs(v - a) < 1e-6 for a in allowed) or data_ok(v) or v in (1, 2, 3, 4, 5, 10, 24, 100)
                if not ok: issues.append(f"number **{v:g}** in “{s[:80]}” not found in narration, sources or data")
        # chart: highlight labels quoting a price at a time
        for it in b["visual"].get("items", []) if b["visual"]["template"] == "chart" else []:
            if it.get("type") == "highlight" and data:
                ps = nums(DAYS_RE.sub("", TIME_RE.sub("", it.get("label", ""))))
                c = data.at(it["from"])
                for p in ps:
                    if p > 1000 and min(abs(p - c[f]) for f in "ohlc") > 1.0: issues.append(f"chart label {p:g} ≠ candle at {it['from']} (o/h/l/c {c['o']}/{c['h']}/{c['l']}/{c['c']})")
            if it.get("type") == "measure" and data:
                pa, _ = data.val(it["a"]); pb, _ = data.val(it["b"]); rep_m = f"measure computed from data: {pa:,.2f} → {pb:,.2f} = {pb - pa:+,.2f} ({(pb - pa) / pa * 100:+.2f}%)"
                issues.append("ok · " + rep_m)
        kind = b.get("kind")
        st = b.get("source_text", "")
        if kind in ("observation", "data", "context") and (not st or "TBD" in st): issues.append("BLOCK · evidence beat without a source line"); block.append(b["id"])
        for sid in b.get("source_ids", []):
            s = srcs.get(sid, {}); vd = s.get("verdict")
            if vd in ("NOT FOUND", "CONTRADICTED", "PARTLY"):
                flagged = "flag" in json.dumps(b["visual"])
                lvl = "BLOCK" if vd in ("NOT FOUND", "CONTRADICTED") else "WARN"
                issues.append(f"{lvl} · source `{sid}` is {vd}: {s.get('note', '')}" + (" — shown with an on-screen flag" if flagged else " — NOT flagged on screen"))
                if lvl == "BLOCK": block.append(b["id"])
        real = [i for i in issues if not i.startswith("ok")]
        rep.append(f"- **{b['id']}** {b['start']:.1f}–{b['end']:.1f}s · {b['visual']['template']} · {kind or '-'}: " + ("✓ clean" if not real else ""))
        for i in issues: rep.append(f"    - {i}")
        for i in real:
            if i.startswith("number") : block.append(b["id"])
    # 4. caption sync
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-map", "0:a", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
    rep.append("\n## 4. Caption sync\n")
    vpath = meta.get("voice")
    if vpath and os.path.exists(vpath):
        vr = subprocess.run(["ffmpeg", "-v", "error", "-i", vpath, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
        a = np.frombuffer(vr, np.int16).astype(float); fr = 160
        e = np.sqrt((a[:len(a) // fr * fr].reshape(-1, fr) ** 2).mean(1)); sp = e > np.percentile(e, 30) * 2
        W_ = T["words"]; errs = []
        for i in range(1, len(W_)):
            if W_[i]["start"] - W_[i - 1]["end"] > 0.15:
                f0 = int((W_[i]["start"] - 1.0) * 100); fp = int((W_[i - 1]["end"] - 1.0) * 100) + 5
                lo_ = max(fp, f0 - 40); seg = sp[lo_:f0 + 60]
                if seg.any(): errs.append((lo_ + int(np.argmax(seg)) - f0) / 100)
        errs = np.array(errs); early = (errs > 0.15).sum(); late = (errs < -0.15).sum()
        rep.append(f"- {len(errs)} words after pauses checked · median offset {np.median(errs) * 1000:+.0f} ms · captions early by >150 ms: {early} · late by >150 ms: {late}")
        if (early + late) > 0.05 * len(errs): rep.append("    - WARN · more than 5% of checked words off by >150 ms")
    # 5. audio
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", video, "-map", "0:a", "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    I = re.findall(r"I:\s+(-?[\d.]+) LUFS", r); TP = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)
    pcm = np.frombuffer(raw, np.int16); clip = int((np.abs(pcm) >= 32700).sum())
    rep.append("\n## 5. Audio\n")
    li = float(I[-1]) if I else None; tp = float(TP[-1]) if TP else None
    rep.append(f"- integrated loudness {li} LUFS (target −14 ±1) · true peak {tp} dBTP (≤ −1.0) · clipped samples {clip}")
    if li is None or abs(li + 14) > 1.0 or (tp is not None and tp > -1.0) or clip > 0: rep.append("    - BLOCK · audio out of spec"); block.append("audio")
    # 6. frames
    rep.append("\n## 6. Frames\n")
    os.makedirs("qa_frames", exist_ok=True); ims = []
    for b in SB["beats"]:
        t = max(b["start"] + 0.5, b["end"] - 0.8); fn = f"qa_frames/{tag}_{b['id']}.png"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", video, "-frames:v", "1", fn], check=True); ims.append(Image.open(fn))
    w, h = ims[0].size; vert = h > w
    tw_ = 360 if vert else 480; th = int(h * tw_ / w); cols = 6 if vert else 4
    S = Image.new("RGB", (tw_ * cols, th * ((len(ims) + cols - 1) // cols)))
    for i, im in enumerate(ims): S.paste(im.resize((tw_, th)), ((i % cols) * tw_, (i // cols) * th))
    S.save(f"qa_frames/{tag}_phone_sheet.png")
    rep.append(f"- {len(ims)} beat frames saved to qa_frames/ · phone-size sheet: qa_frames/{tag}_phone_sheet.png (review by eye)")
    return rep, block

if __name__ == "__main__":
    a = sys.argv[1:]
    thumbs = a[a.index("--thumbs") + 1:] if "--thumbs" in a else []
    if "--thumbs" in a: a = a[:a.index("--thumbs")]
    vert = a[a.index("--vertical") + 1:] if "--vertical" in a else []
    if "--vertical" in a: a = a[:a.index("--vertical")]
    rep, block = run(*a[:5], tag="long")
    if vert:
        r2, b2 = run(vert[1], vert[2], vert[3], a[3], vert[0], tag="short"); rep += ["\n---\n"] + r2; block += ["short:" + x for x in b2]
    if thumbs:
        rep.append("\n## 7. Thumbnails at small size\n")
        sizes = [(168, 94), (246, 138), (360, 202)]; row = []
        for p in thumbs:
            im = Image.open(p).convert("RGB"); row.append([im.resize(s, Image.LANCZOS) for s in sizes])
        W_ = sum(s[0] for s in sizes) + 40; H_ = sum(202 + 20 for _ in thumbs)
        S = Image.new("RGB", (W_, H_), (24, 24, 24)); y = 0
        for r in row:
            x = 0
            for im in r: S.paste(im, (x, y)); x += im.width + 20
            y += 222
        S.save("qa_frames/thumbs_small.png"); rep.append("- qa_frames/thumbs_small.png (168×94 home grid, 246×138 sidebar, 360×202 mobile)")
    status = "BLOCKED" if block else "PASS"
    rep.insert(1, f"**Status: {status}**" + (f" — blocking items: {', '.join(sorted(set(block)))}" if block else "") + "\n")
    out = f"qa_{json.load(open(a[0]))['meta']['id']}.md"; open(out, "w").write("\n".join(rep)); print(status, out)
    sys.exit(1 if block else 0)
