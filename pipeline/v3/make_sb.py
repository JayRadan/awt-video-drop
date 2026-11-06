import json, sys
T = json.load(open("timing.json"))["sentences"]
TT = json.load(open("timing_trailer.json"))["sentences"]
def ix(prefix, S=T):
    for i, s in enumerate(S):
        if s["text"].startswith(prefix): return i
    raise SystemExit("no sentence: " + prefix)
def chart(**k): d = {"template": "chart"}; d.update(k); return d
SRCD = "PAXG-USD 1h, Coinbase (spot-gold proxy), UTC · to 6 Nov 09:00"
meta = {"id": "update_2026-11-06", "format": "16x9", "brand": "ANONYMOUS WOLF TRADER", "vdate": "GOLD · NFP DAY · 6 NOV 2026", "candles": "candles_v.json", "asof": "2026-11-06T09:00", "audio_profile": "energetic", "tail": 2.5, "voice": "voice.mp3"}
B = []
def beat(id, a, b, kind, sb, visual, src=(), stext="", sound=()):
    B.append({"id": id, "sents": [ix(a), ix(b) if isinstance(b, str) else b], "kind": kind, "storyboard": sb, "visual": visual, "source_ids": list(src), "source_text": stext, "sound": list(sound)})
beat("B01", "Today is NFP.", "Don't fall for it.", None, "Hook: cut through the noise.",
     {"template": "title", "kicker": "NFP DAY · 6 NOV", "lines": [{"t": "Every guru is yelling about it.", "at_sent": ix("Every guru")}, {"t": "Don't listen to them.", "col": "gold", "at_sent": ix("First of all")}, {"t": "Don't fall for it.", "col": "muted", "at_sent": ix("Don't fall")}]},
     sound=[{"cue": "riser_hit", "at_sent": ix("First of all"), "dur": 1.0}, {"cue": "hit", "at_sent": ix("Don't fall")}])
beat("B02", "Here's the truth.", "Let's break it down", "interpretation", "The thesis.",
     {"template": "title", "kicker": "THE TRUTH", "lines": [{"t": "Today's NFP is not important.", "at_sent": ix("Today's NFP")}, {"t": "Especially for gold.", "col": "gold", "at_sent": ix("Especially for gold")}]},
     ["analysis"], "My analysis", [{"cue": "silence", "at_sent": ix("Today's NFP"), "dur": 0.4}, {"cue": "hit", "at_sent": ix("Especially for gold")}])
beat("B03", "Since yesterday", "That kind of fall", "data", "The global AI rout in numbers.",
     {"template": "list", "title": "THE AI SELL-OFF · 5–6 NOV", "items": [
         {"t": "Nasdaq −5.5%", "sub": "Thursday close", "col": "red", "at_sent": ix("On Thursday"), "at_word": "nasdaq"},
         {"t": "S&P 500 −4.4% · Dow −3.4%", "sub": "Thursday close · record $2.9 trillion lost", "col": "red", "at_sent": ix("On Thursday"), "at_word": "dow"},
         {"t": "Taiwan −8% at one point", "sub": "closed −4.5% · Friday", "col": "red", "at_sent": ix("And today in Asia"), "at_word": "taiwan"},
         {"t": "Nikkei −5.7%", "sub": "Friday midday", "col": "red", "at_sent": ix("And today in Asia"), "at_word": "nikkei"}]},
     ["foxbiz", "euronews"], "Fox Business 5 Nov · Euronews 6 Nov 2026",
     [{"cue": "hit", "at_sent": ix("On Thursday"), "at_word": "nasdaq"}, {"cue": "hit", "at_sent": ix("And today in Asia"), "at_word": "taiwan"}, {"cue": "riser_hit", "at_sent": ix("That kind of fall"), "at_word": "huge", "dur": 0.8}])
beat("B04", "So first, the reason.", "US, Japan, Taiwan", "context", "The trigger headlines.",
     {"template": "headline", "title": "THE REASON", "items": [
         {"publisher": "Fox Business", "date": "5 Nov 2026", "headline": "Stocks plunge as Dem midterm sweep fuels AI regulatory concerns", "url_short": "Some Democrats called for restrictions or pauses on new data center projects", "at_sent": ix("After winning")},
         {"publisher": "Al Jazeera", "date": "5 Nov 2026", "headline": "AI stocks plunge after US election, driving down markets", "url_short": "39 of 45 data-centre ballot measures passed restrictions", "at_sent": ix("Lower income")}]},
     ["foxbiz", "aljazeera"], "Fox Business · Al Jazeera, 5 Nov 2026",
     [{"cue": "hit", "at_sent": ix("After winning")}, {"cue": "reveal", "at_sent": ix("Lower income")}])
beat("B05", "That made leveraged", "That made leveraged", "interpretation", "The chain reaction.",
     {"template": "mechanism", "title": "WHY STOCKS CRASHED · MY READ", "items": [
         {"t": "No more data-center expansion", "col": "white", "at": 0.1},
         {"t": "Lower AI earnings", "col": "white", "at_sent": ix("That made leveraged"), "at_word": "leveraged"},
         {"t": "Leveraged longs force-sold", "col": "red", "at_sent": ix("That made leveraged"), "at_word": "liquidation"},
         {"t": "Sharp fall", "col": "red", "at_sent": ix("That made leveraged"), "at_word": "sharply"}]},
     ["analysis"], "My analysis", [{"cue": "hit", "at_sent": ix("That made leveraged"), "at_word": "sharply"}])
beat("B06", "But wait a minute.", "Here's why it's strange.", "observation", "Gold during the crash, measured.",
     chart(title="GOLD · 5 → 6 NOV, HOURLY", headline="Why didn't gold crash too?", view=[{"at": 0, "from": "2026-11-05T00:00", "to": "2026-11-06T09:00"}],
           reveal={"keys": [{"at": 0, "until": "2026-11-05T14:00"}, {"at_sent": ix("Why didn't gold"), "until": "2026-11-06T02:00"}, {"at_sent": ix("Isn't that strange"), "until": "2026-11-06T09:00"}]},
           items=[{"type": "highlight", "from": "2026-11-05T14:00", "to": "2026-11-05T20:00", "col": "red", "label": "US STOCKS CRASH", "at_sent": ix("Why didn't gold")},
                  {"type": "measure", "a": {"t": "2026-11-05T14:00", "f": "o"}, "b": {"t": "2026-11-06T02:00", "f": "c"}, "col": "gold", "at_sent": ix("Gold was only down"), "at_word": "1.5", "dur": 0.8}], asof_marker=True),
     ["data_paxg", "euronews"], "5 Nov 14:00 open → 6 Nov 02:00 close · " + SRCD,
     [{"cue": "reveal", "at_sent": ix("Why didn't gold")}, {"cue": "hit", "at_sent": ix("Gold was only down"), "at_word": "1.5"}])
beat("B07", "When we get a shock", "That's why in these situations", "interpretation", "The margin-call mechanism.",
     {"template": "mechanism", "title": "HOW A MARGIN CALL WORKS", "items": [
         {"t": "Shock + forced liquidation", "col": "white", "at_sent": ix("When we get a shock")},
         {"t": "Broker: add capital, or we close you", "col": "white", "at_sent": ix("Either add capital")},
         {"t": "Funds sell their most liquid asset", "col": "gold", "at_sent": ix("They sell the most")},
         {"t": "= GOLD falls even sharper", "col": "red", "at_sent": ix("And that is gold")}]},
     ["analysis"], "How margin calls usually hit gold", [{"cue": "reveal", "at_sent": ix("Either add capital")}, {"cue": "hit", "at_sent": ix("And that is gold")}])
beat("B08", "But look what happened.", "Just 1.5 percent", "observation", "Stocks vs gold, side by side.",
     {"template": "compare", "title": "BUT LOOK WHAT HAPPENED", "left_head": "S&P 500", "right_head": "GOLD", "rows": [
         {"left": "−4.4% in one day", "right": "≈ −1.6%, slowly", "col": "green", "mark": "✓", "at_sent": ix("Just 1.5 percent"), "at_word": "4.4", "at2_sent": ix("Just 1.5 percent")},
         {"left": "Forced liquidation", "right": "Didn't budge", "col": "green", "mark": "", "at_sent": ix("Gold didn't budge"), "at2_sent": ix("Gold didn't budge"), "at2_word": "budge"}]},
     ["foxbiz", "data_paxg"], "S&P 500 close 5 Nov (Fox Business) · gold 5 Nov 14:00 → 6 Nov 02:00 UTC, PAXG-USD 1h",
     [{"cue": "silence", "at_sent": ix("Gold didn't budge"), "dur": 0.4}, {"cue": "hit", "at_sent": ix("Gold didn't budge"), "at_word": "budge"}])
beat("B09", "What does that tell us?", "And if stocks don't fall more", "interpretation", "What it means.",
     {"template": "list", "title": "WHAT THAT TELLS US · MY READ", "items": [
         {"t": "Leverage in stocks washed out yesterday", "col": "white", "at_sent": ix("The majority of high")},
         {"t": "To go lower you need new, fresh money", "col": "white", "at_sent": ix("To go lower")},
         {"t": "Stocks at their lows: who sells here?", "col": "gold", "at_sent": ix("So who is going")},
         {"t": "No margin-call danger for gold", "col": "green", "at_sent": ix("And if stocks don't")}]},
     ["analysis"], "My analysis", [{"cue": "reveal", "at_sent": ix("The majority of high")}, {"cue": "reveal", "at_sent": ix("So who is going")}, {"cue": "hit", "at_sent": ix("And if stocks don't")}])
beat("B10", "I feel like Sherlock", "I feel like Sherlock", None, "A light moment.",
     {"template": "title", "lines": [{"t": "I feel like Sherlock Holmes.", "col": "gold", "at_sent": ix("I feel like Sherlock")}]},
     sound=[{"cue": "hit", "at_sent": ix("I feel like Sherlock"), "at_word": "holmes"}])
beat("B11", "Now, why is NFP", "Even a good NFP", "context", "The Fed view.",
     {"template": "headline", "title": "WHY NFP DOESN'T MATTER · THE FED", "items": [
         {"publisher": "Washington Examiner · on Warsh at Jackson Hole", "date": "1 Sep 2026", "headline": "accelerating business investment, and potentially greater productivity … increasing how fast America can grow without generating inflation", "url_short": "→ strong NFP + flat hourly earnings = no faster hikes (my read)", "at_sent": ix("Warsh argued")}]},
     ["warsh", "analysis"], "Washington Examiner, 1 Sep 2026 · the conclusion is my read", [{"cue": "reveal", "at_sent": ix("Warsh argued")}, {"cue": "hit", "at_sent": ix("Even a good NFP")}])
beat("B12", "Also, yields are falling", "That was the bad scenario", "data", "Yields and FedWatch.",
     {"template": "list", "title": "RATES ARE TELLING US", "items": [
         {"t": "2-year yield −12 bp to 4.46%", "sub": "less AI spending → fewer hikes", "col": "green", "at_sent": ix("Also, yields")},
         {"t": "December hike odds: ~82% → ~66%", "sub": "CME FedWatch", "col": "gold", "at_sent": ix("After the election"), "at_word": "82"},
         {"t": "Hot NFP → back to 80–90%: already expected", "col": "white", "at_sent": ix("If NFP comes in hot")},
         {"t": "The bad scenario for gold is out", "col": "green", "at_sent": ix("That was the bad")}]},
     ["fedwatch", "analysis"], "Pomegra citing CME FedWatch, 6 Nov 2026 · rows 3–4: my read",
     [{"cue": "reveal", "at_sent": ix("Also, yields")}, {"cue": "hit", "at_sent": ix("Now it's around"), "at_word": "66"}, {"cue": "hit", "at_sent": ix("That was the bad")}])
beat("B13", "And if NFP comes in lower?", "So in both cases", "scenario", "Both outcomes.",
     {"template": "compare", "title": "BOTH CASES · MY VIEW", "left_head": "HOT NFP", "right_head": "WEAK NFP", "rows": [
         {"left": "Hike already priced", "right": "Bad news is good news", "col": "green", "mark": "", "at_sent": ix("If NFP comes in hot") if False else ix("And if NFP comes in lower"), "at2_sent": ix("Bad news is good")},
         {"left": "Gold: bullish", "right": "Gold: bullish → spike", "col": "green", "mark": "✓", "at_sent": ix("So in both cases"), "at2_sent": ix("So in both cases"), "at2_word": "bullish"}]},
     ["analysis"], "My analysis", [{"cue": "riser_hit", "at_sent": ix("Boom, spike"), "dur": 0.8}, {"cue": "hit", "at_sent": ix("So in both cases"), "at_word": "bullish"}])
beat("B14", "Now let's check positioning.", "They expect higher prices.", "interpretation", "Positioning on the chart.",
     chart(title="GOLD · 2 → 6 NOV, HOURLY", headline="Positioning · my data read", view=[{"at": 0, "from": "2026-11-02T12:00", "to": "2026-11-06T09:00"}],
           items=[{"type": "zone", "p1": 3900, "p2": 3930, "col": "cyan", "label": "ACCUMULATION 3,900–3,930", "label_x": 0.45, "at_sent": ix("Most of it is around")},
                  {"type": "level", "price": 4100, "col": "red", "label": "NEW LONGS ~4,100 · UNDER WATER", "label_x": 0.05, "at_sent": ix("And surprisingly")},
                  {"type": "note", "text": "≈15K CONTRACTS ADDED · 4–5K AT 4,100 · MY DATA", "col": "gold", "at_sent": ix("About 15 thousand")}], asof_marker=True),
     ["analysis", "data_paxg"], "Positions: my data, not shown · price: " + SRCD,
     [{"cue": "reveal", "at_sent": ix("Most of it is around")}, {"cue": "reveal", "at_sent": ix("And surprisingly")}, {"cue": "hit", "at_sent": ix("But based on everything"), "at_word": "10"}])
beat("B15", "Also, the biggest dealer", "If price breaks above it", "interpretation", "Dealer hedging levels.",
     chart(title="GOLD · 5 → 6 NOV, HOURLY", headline="Dealer hedging · my data read", view=[{"at": 0, "from": "2026-11-05T00:00", "to": "2026-11-06T09:00"}],
           items=[{"type": "level", "price": 4040, "col": "green", "label": "DEALER SUPPORT ~4,040 · POSITIVE DELTA", "label_x": 0.02, "at_sent": ix("Also, the biggest dealer"), "at_word": "4040"},
                  {"type": "level", "price": 4100, "col": "gold", "label": "ACCELERATION ABOVE 4,100", "label_x": 0.02, "at_sent": ix("But the real acceleration")}], asof_marker=True),
     ["analysis", "data_paxg"], "Dealer levels: my data · price: " + SRCD,
     [{"cue": "reveal", "at_sent": ix("Also, the biggest dealer"), "at_word": "4040"}, {"cue": "riser_hit", "at_sent": ix("If price breaks above"), "at_word": "accelerates", "dur": 0.8}])
beat("B16", "And China.", "So China has no fuel", "interpretation", "China.",
     {"template": "title", "kicker": "CHINA · MY DATA", "lines": [{"t": "20,000+ lots closed in 3 days.", "at_sent": ix("In the past three days")}, {"t": "Short take-profit, now longs.", "col": "muted", "at_sent": ix("That's all take profit")}, {"t": "No fuel to push gold down.", "col": "gold", "at_sent": ix("So China has")}]},
     ["analysis"], "My data", [{"cue": "hit", "at_sent": ix("So China has")}])
beat("B17", "So I found no reason", "My target is 4,250", "plan", "The trade on the chart.",
     chart(title="MY TRADE · 6 NOV", headline="Buy 4,040 · stop 1% · target 4,250", view=[{"at": 0, "from": "2026-11-02T12:00", "to": "2026-11-09T00:00"}],
           items=[{"type": "highlight", "from": "2026-11-06T03:00", "col": "green", "label": "BUY 4,040", "label_pos": "below", "at_sent": ix("I'm in a buy"), "at_word": "buy"},
                  {"type": "level", "price": 4000, "col": "red", "label": "STOP −1% ≈ 4,000", "label_x": 0.05, "label_below": True, "at_sent": ix("I'm in a buy"), "at_word": "stop"},
                  {"type": "level", "price": 4250, "col": "gold", "label": "TARGET 4,250 (+5%)", "label_x": 0.05, "at_sent": ix("My target is"), "at_word": "4250"}], asof_marker=True),
     ["analysis", "data_paxg"], "My trade · " + SRCD,
     [{"cue": "hit", "at_sent": ix("I'm in a buy"), "at_word": "buy"}, {"cue": "riser_hit", "at_sent": ix("My target is"), "at_word": "4250", "dur": 1.0}])
beat("B18", "But there is a but.", "If it's super low", "scenario", "The one risk.",
     {"template": "mechanism", "title": "THE <5% RISK · NEGATIVE NFP", "items": [
         {"t": "Very negative NFP = recession fear", "col": "white", "at_sent": ix("If NFP is very bad")},
         {"t": "Algos spike gold & stocks", "col": "green", "at_sent": ix("Algos will buy")},
         {"t": "Positions unwind, stocks fall", "col": "red", "at_sent": ix("But after that spike")},
         {"t": "Margin calls hit gold → get out", "col": "red", "at_sent": ix("Stocks could fall sharply")}]},
     ["analysis"], "My analysis · if NFP is super low or negative, I get out of longs",
     [{"cue": "silence", "at_sent": ix("But there is a but"), "dur": 0.4}, {"cue": "hit", "at_sent": ix("The margin call")}, {"cue": "hit", "at_sent": ix("If it's super low")}])
beat("B19", "That's the whole plan.", "So make sure you control", "plan", "Humility + risk.",
     {"template": "title", "lines": [{"t": "I may be wrong.", "at_sent": ix("I may still be wrong")}, {"t": "That's the market, and probability.", "col": "muted", "at_sent": ix("That's the market")}, {"t": "Control your capital.", "col": "gold", "at_sent": ix("So make sure you control")}]},
     sound=[{"cue": "hit", "at_sent": ix("So make sure you control")}])
beat("B20", "Are you buying", len(T) - 1, None, "Outro.", {"template": "outro", "cta": "Are you buying gold into NFP — or waiting?"}, sound=[{"cue": "outro", "at": 0.2}])
json.dump({"meta": meta, "beats": B}, open("sb.json", "w"), indent=1, ensure_ascii=False)

def tx(p): return ix(p, TT)
tm = dict(meta); tm.update(id="update_2026-11-06_trailer", format="9x16", vdate="GOLD · NFP DAY · 6 NOV", audio_profile="trailer", tail=1.0, voice="voice_trailer.mp3")
S = []
def tb(id, a, b, kind, visual, src=(), stext="", sound=()):
    S.append({"id": id, "sents": [tx(a), tx(b) if isinstance(b, str) else b], "kind": kind, "storyboard": "", "visual": visual, "source_ids": list(src), "source_text": stext, "sound": list(sound)})
tb("S1", "Today is NFP", "For gold", "interpretation", {"template": "title", "kicker": "NFP DAY", "lines": [{"t": "Every guru is yelling.", "at_sent": tx("Today is NFP")}, {"t": "For gold, it's not important.", "col": "gold", "at_sent": tx("For gold")}]}, ["analysis"], "My analysis", [{"cue": "hit", "at_sent": tx("For gold")}])
tb("S2", "Yesterday the Nasdaq", "In a crash like this", "data", {"template": "list", "title": "THE AI CRASH · 5 NOV", "items": [{"t": "Nasdaq −5.5%", "col": "red", "at_sent": tx("Yesterday the Nasdaq")}, {"t": "S&P 500 −4.4%", "col": "red", "at_sent": tx("The S&P 500")}, {"t": "Funds sell gold for margin calls", "col": "gold", "at_sent": tx("In a crash like this")}]}, ["foxbiz"], "Fox Business, 5 Nov 2026", [{"cue": "hit", "at_sent": tx("Yesterday the Nasdaq")}, {"cue": "hit", "at_sent": tx("The S&P 500")}])
tb("S3", "But gold only slipped", "The leverage", "observation", chart(title="GOLD · 5 → 6 NOV", headline="Gold only slipped ~1.5%", view=[{"at": 0, "from": "2026-11-05T00:00", "to": "2026-11-06T09:00"}], items=[{"type": "measure", "a": {"t": "2026-11-05T14:00", "f": "o"}, "b": {"t": "2026-11-06T02:00", "f": "c"}, "col": "gold", "at_sent": tx("But gold only slipped"), "at_word": "1.5", "dur": 0.6}], asof_marker=False), ["data_paxg"], "PAXG-USD 1h, Coinbase, UTC", [{"cue": "riser_hit", "at_sent": tx("But gold only slipped"), "at_word": "1.5", "dur": 0.8}])
tb("S4", "Hot NFP?", "In both cases", "scenario", {"template": "compare", "title": "BOTH CASES", "left_head": "HOT NFP", "right_head": "WEAK NFP", "rows": [{"left": "Hike already priced", "right": "Bad news = good news", "col": "green", "mark": "", "at_sent": tx("The hike is"), "at2_sent": tx("Bad news")}, {"left": "Gold bullish", "right": "Gold bullish", "col": "green", "mark": "✓", "at_sent": tx("In both cases"), "at2_sent": tx("In both cases")}]}, ["analysis"], "My view", [{"cue": "hit", "at_sent": tx("In both cases")}])
tb("S5", "I'm buying at", "My target", "plan", chart(title="MY TRADE", headline="Buy 4,040 → 4,250", view=[{"at": 0, "from": "2026-11-03T00:00", "to": "2026-11-08T00:00"}], items=[{"type": "highlight", "from": "2026-11-06T03:00", "col": "green", "label": "BUY 4,040", "label_pos": "below", "at_sent": tx("I'm buying at")}, {"type": "level", "price": 4000, "col": "red", "label": "STOP −1%", "label_below": True, "at_sent": tx("I'm buying at"), "at_word": "stop"}, {"type": "level", "price": 4250, "col": "gold", "label": "TARGET 4,250", "at_sent": tx("My target")}], asof_marker=False), ["analysis", "data_paxg"], "My trade", [{"cue": "riser_hit", "at_sent": tx("My target"), "at_word": "4250", "dur": 0.8}])
tb("S6", "The only risk", "If that happens", "scenario", {"template": "title", "kicker": "THE ONLY RISK", "lines": [{"t": "Negative NFP → margin-call unwind.", "col": "red", "at_sent": tx("The only risk") + 1 if TT[tx("The only risk")]["text"].endswith(":") else tx("The only risk")}, {"t": "If that happens, get out.", "col": "gold", "at_sent": tx("If that happens")}]}, ["analysis"], "My analysis", [{"cue": "silence", "at_sent": tx("The only risk"), "dur": 0.3}, {"cue": "hit", "at_sent": tx("If that happens")}])
tb("S7", "My own analysis", len(TT) - 1, None, {"template": "title", "lines": [{"t": "My own analysis — not financial advice.", "col": "muted", "at_sent": tx("My own analysis")}]}, [], "", [{"cue": "outro", "at_sent": tx("My own analysis")}])
json.dump({"meta": tm, "beats": S}, open("sb_trailer.json", "w"), indent=1, ensure_ascii=False)
print("ok", len(B), len(S))
