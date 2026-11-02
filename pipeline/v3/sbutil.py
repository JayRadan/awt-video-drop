"""Storyboard helpers shared by engine3, sfx3, qa and the storyboard exporter.
A beat groups adjacent sentences that one visual explains: {"id", "sents": [i0, i1], "kind", "visual", "sound", "source_ids", "source_text"}.
Any dict inside a beat may time itself with "at_sent": <sentence index> and optional "at_word": "<word prefix>";
these resolve to "at" = seconds from the beat start, so reveals land on the spoken word.
"""
import json, re

def _norm(w): return re.sub(r"[^a-z0-9]", "", w.lower())

def word_time(T, si, prefix=None):
    ws = [w for w in T["words"] if w["sent"] == si]
    if not ws: return T["sentences"][si]["start"]
    if prefix:
        p = _norm(prefix)
        for w in ws:
            if _norm(w["w"]).startswith(p): return w["start"]
    return ws[0]["start"]

def _resolve(obj, T, b0):
    if isinstance(obj, dict):
        if "at_sent" in obj:
            obj["at"] = round(max(0.0, word_time(T, obj["at_sent"], obj.get("at_word")) - b0) + obj.get("plus", 0.0), 2)
        for k in ("at2_sent",):
            if k in obj: obj["at2"] = round(max(0.0, word_time(T, obj[k], obj.get("at2_word")) - b0), 2)
        if "focus_sents" in obj:
            a, b = obj["focus_sents"]; obj["focus"] = [T["sentences"][a]["start"] - b0, T["sentences"][b]["end"] - b0 + 0.3]
        for v in obj.values(): _resolve(v, T, b0)
    elif isinstance(obj, list):
        for v in obj: _resolve(v, T, b0)

def load(sb_path, timing_path):
    SB = json.load(open(sb_path)); T = json.load(open(timing_path)); S = T["sentences"]
    beats = SB["beats"]
    for i, b in enumerate(beats):
        b["start"] = 0.0 if i == 0 else S[b["sents"][0]]["start"] - 0.05
    for i, b in enumerate(beats):
        b["end"] = beats[i + 1]["start"] if i + 1 < len(beats) else S[b["sents"][1]]["end"] + SB["meta"].get("tail", 2.0)
        b["narration"] = " ".join(S[k]["text"] for k in range(b["sents"][0], b["sents"][1] + 1))
        _resolve(b, T, b["start"])
    # sanity: beats must cover every sentence exactly once, in order
    cov = [k for b in beats for k in range(b["sents"][0], b["sents"][1] + 1)]
    assert cov == list(range(len(S))), f"beats do not cover sentences 0..{len(S)-1} in order"
    return SB, T
