"""Scene plan for the 22 Oct 2026 video — engine v2 templates."""
GOLD = (242, 193, 78); RED = (255, 77, 77); GREEN = (46, 230, 166); WHITE = (238, 241, 248)

PLAN = [
    # 0 hook — AI bumper if present, else hero chart with headline
    {"para": 0, "template": "bumper", "hook": "SOMEONE WAS ABSORBING THE BUYERS AT 4,150.|TODAY GOLD FELL $80. HERE'S THE PLAN."},
    # 1 recap: the trade — hero chart with entries drawn in, breakdown shown
    {"para": 1, "template": "hero_chart", "title": "GOLD · 1H · THE SHORT, SO FAR", "level": True, "level2": True,
     "entries": [(4190, GREEN, "CORE SHORT · ~4,190 SPOT · 4 DAYS AGO", 8), (4140, GREEN, "ADDED · ~4,140 SPOT · YESTERDAY", 14)],
     "headline": "THE TRADE|IN PROFIT · SCALING OUT"},
    # 2 the plan: five things — impact card
    {"para": 2, "template": "impact", "kicker": "THE PLAN FROM HERE", "value": "5", "sub": "THINGS THAT DECIDE THE NEXT MOVE|seasonality · positioning · headlines · stocks · the next wall", "col": GOLD},
    # 3 seasonality — timeline
    {"para": 3, "template": "timeline", "title": "1 · SEASONALITY · GOLD'S TYPICAL YEAR (SHAPE, NOT DATA)", "highlight": [10, 11, 0, 1], "negative": [9],
     "callouts": [{"text": "WORST MONTH", "x": 1230, "y": 190, "col": RED, "at": 3},
                  {"text": "LATE OCT → LATE FEB · WINTER RALLY · AVG ≈ +9.5%", "x": 760, "y": 250, "col": GOLD, "at": 9, "f": "h3"},
                  {"text": "DIWALI NOV 8 · JEWELLERY · NEW-YEAR FLOWS", "x": 760, "y": 300, "col": WHITE, "at": 13, "f": "sm"},
                  {"text": "TURN: START OF NOVEMBER", "x": 130, "y": 185, "col": GOLD, "at": 22, "f": "h2"}],
     "note": "Caveat: a tendency, not a timer — October 2025 was the strongest month of the cycle (+10%).", "note_at": 18},
    # 4 positioning — kinetic quote on the squeeze sentence
    {"para": 4, "template": "quote", "kicker": "2 · POSITIONING — WILL THE BIG SHORTS COVER?", "hot": ["SHORT", "SQUEEZE", "FUEL", "BETTER"]},
    # 5 headlines — split with oil/yields rows + the Oct 20 example
    {"para": 5, "template": "split", "title": "GOLD · 1H", "headline": "3 · HEADLINE SHOCKS", "panel_title": "OIL & YIELDS RISING",
     "rows": [{"k": "OIL", "v": "RISING", "col": RED, "at": 1, "h": 90}, {"k": "YIELDS", "v": "RISING", "col": RED, "at": 2, "h": 90},
              {"k": "20 OCT · HEADLINE", "v": "US–IRAN “CLOSE TO AGREEMENT”", "sub": "oil −6% in minutes", "col": WHITE, "at": 7, "h": 120},
              {"k": "30 MIN LATER · IRAN", "v": "“NO AGREEMENT”", "sub": "the move reversed", "col": GOLD, "at": 13, "h": 120}],
     "footer": "BE READY FOR HEADLINE SHOCKS", "footer_at": 17},
    # 6 stocks — chain with sparklines
    {"para": 6, "template": "chain", "headline": "4 · VIX RISING WHILE THE DOW RISES",
     "items": [{"t": "STOCKS HOLD UP", "sub": "rise continued 54–68% of the time", "col": GREEN, "at": 12},
               {"t": "NO MARGIN CALLS", "sub": "no crash soon", "col": GREEN, "at": 15},
               {"t": "NO FORCED GOLD SELLING", "sub": "gold is first to go in a margin call", "col": GREEN, "at": 18},
               {"t": "NOVEMBER BOUNCE", "sub": "becomes more likely", "col": GOLD, "at": 21}],
     "sparks": [{"label": "DOW", "col": GREEN, "drift": 0.012, "seed": 3, "at": 1}, {"label": "VIX", "col": RED, "drift": 0.010, "seed": 8, "at": 2}],
     "footer": "RARE: 13–38 DAYS PER DECADE SINCE 1995", "footer_at": 4},
    # 7 the next wall — hero chart zoomed, level2 and breakdown into it
    {"para": 7, "template": "hero_chart", "title": "GOLD · 1H · THE NEXT WALL", "zoom": 0.6, "level": True, "level2": True, "break_at": 4,
     "headline": "5 · THE PUT WALL AT 4,000 FUT / 3,980 SPOT|A DROP INTO IT SLOWS OR BOUNCES — THE CUSHION"},
    # 8 the plan — cards
    {"para": 8, "template": "cards", "headline": "THE PLAN", "level2": True, "zoom": 0.3,
     "items": [{"t": "SCALE OUT SLOWLY", "sub": "final target 4,000 – 3,980 spot", "col": GOLD, "at": 0.8},
               {"t": "WATCH THE BIG SHORTS", "sub": "if they don't cover — squeeze fuel", "at": 3.5},
               {"t": "EXPECT HEADLINE SHOCKS", "sub": "oil & yields", "at": 6.5},
               {"t": "STOCKS HOLDING UP", "sub": "removes margin-call risk for gold", "at": 9.5},
               {"t": "PUT WALL AT 4,000", "sub": "where the November bounce can start", "col": GREEN, "at": 13}]},
    # 9 outro
    {"para": 9, "template": "outro"},
]
