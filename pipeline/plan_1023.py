"""Scene plan — 23 Oct 2026: target hit, flat, waiting for 4,050 pullback."""
GOLD = (242, 193, 78); RED = (255, 77, 77); GREEN = (46, 230, 166); WHITE = (238, 241, 248)

PLAN = [
    # 0 hook over the chart (zoomed to the drop into the wall)
    {"para": 0, "template": "bumper", "hook": "YESTERDAY'S TARGET: 4,000 – 3,980.|OVERNIGHT, GOLD HIT IT. I'M FLAT."},
    # 1 recap of the trade: entries + exit at the wall
    {"para": 1, "template": "hero_chart", "title": "GOLD · 1H · THE TRADE, START TO FINISH", "level": True, "level2": True,
     "entries": [(4190, GREEN, "CORE SHORT · ~4,190 SPOT", 3), (4140, GREEN, "ADDED · ~4,140 SPOT", 6), (3997, GOLD, "OVERNIGHT LOW · 3,997 · CLOSED", 12)],
     "headline": "TARGET HIT|+2,000 PIPS · SHORT CLOSED"},
    # 2 pointer to previous video
    {"para": 2, "template": "cards", "headline": "THE PLAN BEHIND IT", "zoom": 0.0, "level2": True, "row_h": 110,
     "items": [{"t": "SEASONALITY", "sub": "late-October turn", "at": 1.0}, {"t": "POSITIONING", "sub": "will the big shorts cover?", "at": 2.2},
               {"t": "HEADLINES", "sub": "oil & yields", "at": 3.4}, {"t": "THE STOCK MARKET", "sub": "VIX up, Dow up", "at": 4.6},
               {"t": "THE OPTION WALL", "sub": "4,000 fut / 3,980 spot — the cushion", "col": GOLD, "at": 5.8},
               {"t": "FULL BREAKDOWN → PREVIOUS VIDEO", "sub": "link in description & pinned comment", "col": GREEN, "at": 8.0}]},
    # 3 no new short from here — split with reasons
    {"para": 3, "template": "split", "title": "GOLD · 1H · SITTING ON THE WALL", "zoom": 0.7, "level2": True, "headline": "NO NEW SHORT FROM HERE", "panel_title": "WHY",
     "rows": [{"k": "PRICE", "v": "ON THE PUT WALL", "sub": "where the hedgers sit", "col": GOLD, "at": 1.5, "h": 110},
              {"k": "IF IT FALLS", "v": "TAPPED & LIMITED", "sub": "the move won't run far", "col": WHITE, "at": 6.0, "h": 110},
              {"k": "A SHORT HERE", "v": "LITTLE ROOM, A LOT OF RISK", "col": RED, "at": 11.0, "h": 110}],
     "footer": "MAYBE A BIT LOWER — BUT NOT WORTH CHASING", "footer_at": 3.0},
    # 4 the exception — kinetic quote
    {"para": 4, "template": "quote", "kicker": "THE ONE EXCEPTION", "hot": ["PULLBACK", "SELL", "ORDERS", "BOTH", "TOGETHER", "OUT"]},
    # 5 the level: 4,050 — impact card
    {"para": 5, "template": "impact", "kicker": "THE PULLBACK LEVEL I'M WATCHING", "count": (3997, 4050), "fmt": "{:,.0f}", "sub": "SPOT|a new short only if the big sell orders are still there", "col": GOLD},
    # 6 otherwise: the November plan — chain
    {"para": 6, "template": "chain", "headline": "IF THE PULLBACK DOESN'T COME: THE PLAN STANDS",
     "items": [{"t": "NOVEMBER TURN", "sub": "seasonal turning point", "col": GOLD, "at": 2}, {"t": "BIG SHORTS COVER?", "sub": "squeeze fuel if not", "col": WHITE, "at": 5},
               {"t": "OIL & YIELD HEADLINES", "sub": "expect shocks", "col": WHITE, "at": 8}, {"t": "STOCKS HOLD UP", "sub": "no margin-call selling", "col": GREEN, "at": 11}],
     "footer": "TARGET REACHED FASTER THAN EXPECTED — THAT'S ALL", "footer_at": 14},
    # 7 summary cards
    {"para": 7, "template": "cards", "headline": "PUT SIMPLY", "zoom": 0.5, "level2": True,
     "items": [{"t": "SHORT CLOSED AT TARGET", "sub": "+2,000 pips", "col": GREEN, "at": 1.0}, {"t": "NO NEW SHORT FROM HERE", "sub": "the wall limits the downside", "col": RED, "at": 4.0},
               {"t": "NEW SHORT ONLY ON A PULLBACK", "sub": "~4,050 spot, with big sell orders still coming in", "col": GOLD, "at": 7.5},
               {"t": "OTHERWISE: PATIENCE", "sub": "the November plan stands", "at": 11.5}]},
    # 8 "best trade is no trade" — hero chart calm, full range
    {"para": 8, "template": "hero_chart", "title": "GOLD · 1H", "level": True, "level2": True, "headline": "SOMETIMES THE BEST TRADE IS NO TRADE|LET THE MARKET SHOW THE NEXT SETUP"},
    # 9 outro
    {"para": 9, "template": "outro"},
]
