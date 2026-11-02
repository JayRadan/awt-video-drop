"""Export a storyboard to a self-contained HTML review document (one row per beat, every sentence listed).
Usage: python3 sb_export.py storyboard.json timing.json sources.json frames_dir out.html"""
import sys, json, base64, io, os, html
from PIL import Image
import sbutil
SB, T = sbutil.load(sys.argv[1], sys.argv[2]); SRC = json.load(open(sys.argv[3]))["sources"]; FR = sys.argv[4]; OUT = sys.argv[5]
S = T["sentences"]
def thumb(bid):
    for pre in ("long_", "short_", ""):
        p = os.path.join(FR, f"{pre}{bid}.png")
        if os.path.exists(p):
            im = Image.open(p).convert("RGB"); im.thumbnail((420, 420)); b = io.BytesIO(); im.save(b, "JPEG", quality=78)
            return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()
    return ""
def anim(v):
    out = []
    t = v["template"]
    if t == "chart":
        vw = v.get("view", [])
        if vw: out.append("camera: " + " → ".join(f"{k['from'][5:16].replace('T',' ')}–{k['to'][5:16].replace('T',' ')} @{k['at']:.1f}s" for k in vw))
        if v.get("reveal"): out.append(f"reveal candles over {v['reveal'].get('dur',2)}s")
        for it in v.get("items", []):
            lab = it.get("label") or it.get("text") or ""
            out.append(f"@{it.get('at',0):.1f}s {it['type']}" + (f" {it.get('price','')}" if it['type']=='level' else "") + (f" “{lab}”" if lab else ""))
    else:
        for key in ("items", "rows", "lines", "more", "less"):
            for it in v.get(key, []):
                lab = it.get("t") or it.get("value") or it.get("left") or it.get("name") or it.get("headline") or ""
                out.append(f"@{it.get('at',0):.1f}s {html.escape(str(lab))[:70]}" + (f" ⚠{it['flag']}" if it.get("flag") else ""))
    return "<br>".join(out)
rows = []
for b in SB["beats"]:
    sents = "".join(f"<li><span class=t>{S[i]['start']:.1f}s</span> {html.escape(S[i]['text'])}</li>" for i in range(b["sents"][0], b["sents"][1] + 1))
    srcs = []
    for sid in b.get("source_ids", []):
        s = SRC.get(sid, {}); vd = s.get("verdict", "")
        url = (s.get("url") or "").split(" ; ")[0]
        srcs.append(f"<div class='src {vd.replace(' ','_')}'><b>{html.escape(s.get('publisher', s.get('what', sid)))}</b> {html.escape(s.get('date',''))} {('· <a href=\"'+url+'\">link</a>') if url else ''} {('<span class=vd>'+vd+'</span>') if vd else ''}{('<div class=note>'+html.escape(s.get('note',''))+'</div>') if s.get('note') else ''}</div>")
    snd = ", ".join(f"{c['cue']}@{c.get('at',0):.1f}s" for c in b.get("sound", [])) or "—"
    img = thumb(b["id"])
    rows.append(f"<tr><td class=id>{b['id']}<div class=k>{b.get('kind') or ''}</div><div class=dur>{b['start']:.1f}–{b['end']:.1f}s<br><b>{b['end']-b['start']:.1f}s</b></div></td>"
                f"<td><ol>{sents}</ol></td><td><b>{b['visual']['template']}</b><div class=sb>{html.escape(b.get('storyboard',''))}</div>{('<img src='+img+'>') if img else ''}</td>"
                f"<td class=an>{anim(b['visual'])}</td><td>{''.join(srcs) or '—'}<div class=st>{html.escape(b.get('source_text',''))}</div></td><td>{snd}</td></tr>")
doc = f"""<!doctype html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>Storyboard {SB['meta']['id']}</title>
<style>body{{background:#0b0d12;color:#e6e8ee;font:14px/1.45 Inter,system-ui,sans-serif;margin:24px}}h1{{font-size:22px}}table{{border-collapse:collapse;width:100%}}
td,th{{border-bottom:1px solid #222a3a;vertical-align:top;padding:10px 8px}}th{{text-align:left;color:#8a93a8;font-weight:600;position:sticky;top:0;background:#0b0d12}}
.id{{font-weight:700;color:#f2c14e;white-space:nowrap}}.k{{color:#8a93a8;font-weight:500;font-size:12px}}.dur{{color:#8a93a8;font-size:12px;margin-top:6px}}
ol{{margin:0;padding-left:18px}}.t{{color:#6b7488;font-size:12px}}img{{display:block;margin-top:8px;max-width:420px;border-radius:6px}}.sb{{color:#b8c0d0;margin:4px 0}}
.an{{font-size:12px;color:#b8c0d0}}.src{{margin-bottom:6px}}.vd{{font-size:11px;padding:1px 6px;border-radius:4px;margin-left:4px;background:#1e3a2e;color:#5fe0b0}}
.NOT_FOUND .vd,.CONTRADICTED .vd{{background:#4a1616;color:#ff8a8a}}.PARTLY .vd{{background:#4a3a10;color:#ffd166}}.note{{font-size:12px;color:#ffb44a}}.st{{font-size:12px;color:#8a93a8}}a{{color:#7cc4ff}}</style></head>
<body><h1>Storyboard · {SB['meta']['id']}</h1><p>{len(SB['beats'])} beats · {len(S)} sentences · {SB['beats'][-1]['end']:.0f}s · format {SB['meta'].get('format')} · as-of {SB['meta'].get('asof','')} UTC</p>
<table><tr><th>Beat</th><th>Narration (every sentence)</th><th>Visual</th><th>Animation / camera</th><th>Sources</th><th>Sound</th></tr>{''.join(rows)}</table></body></html>"""
open(OUT, "w").write(doc); print("wrote", OUT, len(doc) // 1024, "KB")
