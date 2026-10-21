#!/usr/bin/env python3
"""Fetch hourly XAUUSD candles from Dukascopy's public datafeed and write candles.json.
Usage: python3 fetch_duka.py <days_back> [out.json]
Format: each day file BID_candles_hour_1.bi5 = LZMA-compressed records of 24 bytes:
  int32 seconds-from-day-start, int32 open, int32 close, int32 low, int32 high (price*1000), float32 volume (big-endian)
Month in the URL is 0-based.
"""
import sys, lzma, struct, json, datetime, urllib.request, time

SYM = "XAUUSD"; SCALE = 1000.0
days = int(sys.argv[1]) if len(sys.argv) > 1 else 21
out = sys.argv[2] if len(sys.argv) > 2 else "candles.json"
today = datetime.datetime.utcnow().date()
candles = []
missing = []
for k in range(days, -1, -1):
    d = today - datetime.timedelta(days=k)
    url = f"https://datafeed.dukascopy.com/datafeed/{SYM}/{d.year}/{d.month-1:02d}/{d.day:02d}/BID_candles_hour_1.bi5"
    try:
        req = urllib.request.Request(url)
        raw = urllib.request.urlopen(req, timeout=30).read()
    except Exception as e:
        missing.append((str(d), str(e)[:60])); continue
    if not raw:
        continue
    data = lzma.decompress(raw)
    day_start = datetime.datetime(d.year, d.month, d.day)
    for i in range(0, len(data), 24):
        t, o, c, lo, hi, v = struct.unpack(">iiiiif", data[i:i+24])
        ts = day_start + datetime.timedelta(seconds=t)
        candles.append({"t": ts.strftime("%Y-%m-%dT%H:%M"), "o": o/SCALE, "h": hi/SCALE, "l": lo/SCALE, "c": c/SCALE, "v": round(v, 2)})
    time.sleep(0.15)
json.dump({"symbol": SYM, "interval": "1h", "fetched": datetime.datetime.utcnow().isoformat(), "candles": candles}, open(out, "w"))
print(f"{len(candles)} candles, {len(missing)} missing days")
for m in missing[:5]: print("  missing", m)
if candles:
    print("first", candles[0]); print("last", candles[-1])
