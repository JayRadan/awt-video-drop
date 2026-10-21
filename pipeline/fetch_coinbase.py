#!/usr/bin/env python3
"""Fetch hourly PAXG-USD (tokenized gold, tracks spot XAUUSD within ~0.1-0.3%) from Coinbase Exchange -> candles.json
Usage: python3 fetch_coinbase.py <hours> [out.json]
No API key. 300 candles per request; two requests cover ~17 days. Uses curl (urllib's default agent is refused by the CDN).
"""
import sys, json, datetime, subprocess, time

hours = int(sys.argv[1]) if len(sys.argv) > 1 else 400
out = sys.argv[2] if len(sys.argv) > 2 else "candles.json"
PRODUCT = "PAXG-USD"
now = datetime.datetime.now(datetime.timezone.utc).replace(second=0, microsecond=0)
rows, end = {}, now
while len(rows) < hours:
    start = end - datetime.timedelta(hours=300)
    url = (f"https://api.exchange.coinbase.com/products/{PRODUCT}/candles?granularity=3600"
           f"&start={start:%Y-%m-%dT%H:%M:%SZ}&end={end:%Y-%m-%dT%H:%M:%SZ}")
    txt = subprocess.run(["curl", "-sS", "-m", "30", url], capture_output=True, text=True).stdout
    try:
        data = json.loads(txt)
    except Exception:
        print("bad response:", txt[:200]); sys.exit(2)
    if not isinstance(data, list) or not data:
        break
    for t, lo, hi, o, c, v in data:
        rows[t] = (o, hi, lo, c, v)
    end = start
    time.sleep(0.5)
cands = [{"t": datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M"),
          "o": r[0], "h": r[1], "l": r[2], "c": r[3], "v": round(r[4], 3)} for t, r in sorted(rows.items())][-hours:]
json.dump({"symbol": PRODUCT, "interval": "1h", "source": "Coinbase Exchange", "fetched": now.isoformat(), "candles": cands}, open(out, "w"))
print(len(cands), "candles", cands[0]["t"], "->", cands[-1]["t"], "last close", cands[-1]["c"])
