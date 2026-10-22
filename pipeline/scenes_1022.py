"""Scene set for the 22 Oct 2026 video. Loaded by engine.py when SCENES=scenes_1022 is set:
defines render_scene(p, lt, t, s, ctx) -> True if handled. ctx gives access to the engine kit."""
import os, math

def render_scene(p, lt, t, s, c):
    d, g, base = c["d"], c["g"], c["base"]
    W, H, F = c["W"], c["H"], c["F"]
    ease, alpha, mix, rr, tw, big_label = c["ease"], c["alpha"], c["mix"], c["rr"], c["tw"], c["big_label"]
    chart, topbar, ticker, caption = c["chart"], c["topbar"], c["ticker"], c["caption"]
    GOLD, RED, GREEN, WHITE, MUTED, PANEL, PANEL2, GRID2, BG, DIM = c["GOLD"], c["RED"], c["GREEN"], c["WHITE"], c["MUTED"], c["PANEL"], c["PANEL2"], c["GRID2"], c["BG"], c["DIM"]
    CHART_BOX, SIDE_BOX = c["CHART_BOX"], c["SIDE_BOX"]
    C, LEVEL, N = c["C"], c["LEVEL"], c["N"]
    u = ease(lt / 0.5)
    L2 = float(os.environ.get("LEVEL2", "3980"))   # put wall spot
    ENTRY1 = 4190.0; ENTRY2 = 4140.0

    def side(title):
        x0, y0, x1, y1 = SIDE_BOX; rr(d, SIDE_BOX, 10, PANEL, outline=GRID2)
        d.text((x0 + 20, y0 + 16), title, font=F["tag"], fill=MUTED); return x0, y0, x1, y1

    def hline(py, price, col, label, u_=1.0, x0=CHART_BOX[0], x1=CHART_BOX[2] - 120):
        y = py(price)
        for xx in range(x0 + 12, x1, 28): d.line([(xx, y), (min(xx + 16, x1), y)], fill=alpha(col, u_), width=3)
        lw = tw(d, label, F["tag"]); rr(d, [x0 + 24, y - 40, x0 + 24 + lw + 30, y - 8], 6, alpha(PANEL2, u_), outline=alpha(col, u_))
        d.text((x0 + 39, y - 34), label, font=F["tag"], fill=alpha(col, u_))

    if p == 1:  # recap: the trade. 4150 wall, entries, current price, TP zone
        topbar(d, g, t, u); ticker(d, t, u)
        px, py = chart(d, g, CHART_BOX, t, title="GOLD · 1H · THE SHORT, SO FAR", level=True, level_u=1.0, wall=True, rejections=False)
        if lt > 1.5: hline(py, ENTRY1, GREEN, "CORE SHORT  ·  ~4,190 SPOT  ·  4 DAYS AGO", ease((lt - 1.5) / 0.5))
        if lt > 4.0: hline(py, ENTRY2, GREEN, "ADDED  ·  ~4,140 SPOT  ·  YESTERDAY", ease((lt - 4.0) / 0.5))
        x0, y0, x1, y1 = side("THE TRADE")
        rows = [("CORE SHORT", "~4,190 spot", 1.5), ("ADDED", "~4,140 spot", 4.0), ("NOW", f"~{C[-1][3]:,.0f} spot", 6.5), ("FINAL TP ZONE", "4,000 – 3,980 spot", 9.5)]
        for i, (a, b, at) in enumerate(rows):
            v = ease((lt - at) / 0.5); yy = y0 + 70 + i * 130
            rr(d, [x0 + 20, yy, x1 - 20, yy + 108], 8, alpha(PANEL2, v), outline=alpha(GOLD if i == 3 else GRID2, v))
            d.text((x0 + 40, yy + 14), a, font=F["sm"], fill=alpha(MUTED, v))
            big_label(d, g, x0 + 40, yy + 46, b, GOLD if i == 3 else (GREEN if i < 2 else WHITE), v, "h3")
        v = ease((lt - 12) / 0.6); d.text((x0 + 20, y1 - 60), "scaling out slowly from here", font=F["sm"], fill=alpha(GOLD, v))
        caption(d, g, t); return True

    if p == 2:  # the plan: five pillars
        topbar(d, g, t, u); ticker(d, t, u)
        chart(d, g, CHART_BOX, t, title="GOLD · 1H", level=True)
        big_label(d, g, 70, 150, "THE PLAN FROM HERE", WHITE, ease(lt / 0.6), "h2")
        x0, y0, x1, y1 = side("FIVE THINGS")
        items = ["SEASONALITY", "POSITIONING", "MACRO HEADLINES", "THE STOCK MARKET", "THE NEXT OPTION WALL"]
        for i, a in enumerate(items):
            v = ease((lt - 1.2 - i * 0.6) / 0.5); yy = y0 + 70 + i * 130
            big_label(d, g, x0 + 24, yy, str(i + 1), GOLD, v, "h1")
            d.text((x0 + 100, yy + 22), a, font=F["h3"], fill=alpha(WHITE, v))
        caption(d, g, t); return True

    if p == 3:  # seasonality: month bars Oct worst, Nov-Feb rally
        topbar(d, g, t, u); ticker(d, t, u)
        x0, y0, x1, y1 = (40, 110, 1340, 870); rr(d, (x0, y0, x1, y1), 10, PANEL, outline=GRID2)
        d.text((x0 + 24, y0 + 16), "1 · SEASONALITY  ·  GOLD'S TYPICAL YEAR (ILLUSTRATIVE SHAPE)", font=F["tag"], fill=MUTED)
        months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
        vals = [0.7, 0.6, 0.1, 0.2, 0.0, -0.1, 0.4, 0.5, 0.3, -0.6, 0.6, 0.6]  # tendency only, not data
        bw = (x1 - x0 - 120) / 12; base_y = y0 + 520
        for i, (m, v_) in enumerate(zip(months, vals)):
            vv = ease((lt - 0.6 - i * 0.15) / 0.5)
            xx = x0 + 60 + i * bw; h_ = v_ * 260 * vv
            col = RED if v_ < 0 else (GOLD if i in (10, 11, 0, 1) else mix(BG, GREEN, 0.7))
            d.rectangle([xx + 8, min(base_y, base_y - h_), xx + bw - 8, max(base_y, base_y - h_)], fill=alpha(col, vv))
            d.text((xx + bw / 2 - tw(d, m, F["sm"]) / 2, base_y + 16), m, font=F["sm"], fill=alpha(GOLD if i >= 9 or i <= 1 else DIM, vv))
        d.line([(x0 + 40, base_y), (x1 - 40, base_y)], fill=GRID2, width=1)
        if lt > 3:
            v = ease((lt - 3) / 0.5); xx = x0 + 60 + 9 * bw
            rr(d, [xx - 10, y0 + 70, xx + bw + 10, y0 + 120], 6, alpha((60, 18, 20), v), outline=alpha(RED, v))
            d.text((xx + bw / 2 - tw(d, "WORST MONTH", F["tag"]) / 2, y0 + 84), "WORST MONTH", font=F["tag"], fill=alpha(RED, v))
        if lt > 8:
            v = ease((lt - 8) / 0.6); xa = x0 + 60 + 10 * bw - 30; xb = x0 + 60 + 2 * bw
            d.line([(xa, y0 + 200), (x1 - 60, y0 + 200)], fill=alpha(GOLD, v), width=4)
            d.polygon([(x1 - 60, y0 + 186), (x1 - 60, y0 + 214), (x1 - 32, y0 + 200)], fill=alpha(GOLD, v))
            d.text((xa, y0 + 150), "LATE OCT → LATE FEB  ·  WINTER RALLY  ·  AVG ≈ +9.5% (BULL YEARS)", font=F["tag"], fill=alpha(GOLD, v))
        if lt > 14:
            v = ease((lt - 14) / 0.6)
            d.text((x0 + 60, y1 - 60), "Caveat: seasonality is a tendency, not a timer. October 2025 was the strongest month of the cycle (+10%).", font=F["sm"], fill=alpha(MUTED, v))
        sx0, sy0, sx1, sy1 = side("DEMAND DRIVERS")
        drv = [("DIWALI · NOV 8", "Indian festival & wedding demand", 10), ("HOLIDAY JEWELLERY", "Western seasonal buying", 11.5), ("NEW-YEAR FLOWS", "investment allocations", 13)]
        for i, (a, b, at) in enumerate(drv):
            v = ease((lt - at) / 0.5); yy = sy0 + 70 + i * 120
            rr(d, [sx0 + 20, yy, sx1 - 20, yy + 96], 8, alpha(PANEL2, v), outline=alpha(GOLD, v * 0.6))
            d.text((sx0 + 36, yy + 14), a, font=F["h3"], fill=alpha(GOLD, v)); d.text((sx0 + 36, yy + 58), b, font=F["sm"], fill=alpha(MUTED, v))
        v = ease((lt - 18) / 0.6); big_label(d, g, sx0 + 20, sy1 - 150, "TURN: START", GOLD, v, "h2"); big_label(d, g, sx0 + 20, sy1 - 95, "OF NOVEMBER", WHITE, v, "h2")
        caption(d, g, t); return True

    if p == 4:  # positioning: will the big shorts cover? squeeze fuel
        topbar(d, g, t, u); ticker(d, t, u)
        chart(d, g, CHART_BOX, t, title="GOLD · 1H", level=True, zoom_u=0.0)
        big_label(d, g, 70, 150, "2 · POSITIONING", WHITE, ease(lt / 0.6), "h2")
        x0, y0, x1, y1 = side("THE BIG SHORTS")
        d.text((x0 + 20, y0 + 60), "Do they take profit like us?", font=F["h3"], fill=alpha(WHITE, ease((lt - 1) / 0.5)))
        a_ = [("IF THEY COVER", "fine — bounce starts cleanly", GREEN, 3.5), ("IF THEY DON'T", "even better: fuel for a short squeeze", GOLD, 6.5)]
        for i, (h1, h2, col, at) in enumerate(a_):
            v = ease((lt - at) / 0.5); yy = y0 + 130 + i * 150
            rr(d, [x0 + 20, yy, x1 - 20, yy + 120], 8, alpha(PANEL2, v), outline=alpha(col, v * 0.7))
            d.text((x0 + 36, yy + 16), h1, font=F["h3"], fill=alpha(col, v)); d.text((x0 + 36, yy + 66), h2, font=F["sm"], fill=alpha(MUTED, v))
        v = ease((lt - 10) / 0.6)
        d.text((x0 + 20, y0 + 460), "my read: they get out soon", font=F["h3"], fill=alpha(WHITE, v))
        big_label(d, g, x0 + 20, y0 + 520, "PREPARE THE", GOLD, v, "h2"); big_label(d, g, x0 + 20, y0 + 575, "NOVEMBER REBOUND", GOLD, v, "h2")
        caption(d, g, t); return True

    if p == 5:  # headlines: oil & yields, Oct 20 example
        topbar(d, g, t, u); ticker(d, t, u)
        x0, y0, x1, y1 = (40, 110, 1340, 870); rr(d, (x0, y0, x1, y1), 10, PANEL, outline=GRID2)
        d.text((x0 + 24, y0 + 16), "3 · MACRO HEADLINES  ·  OIL & YIELDS RISING", font=F["tag"], fill=MUTED)
        # two rising arrows
        for i, (lab, at) in enumerate([("OIL", 0.8), ("YIELDS", 1.4)]):
            v = ease((lt - at) / 0.6); cx = x0 + 260 + i * 420
            d.line([(cx, y0 + 420), (cx, y0 + 420 - 240 * v)], fill=alpha(RED, v), width=14)
            d.polygon([(cx - 40, y0 + 190 + 240 * (1 - v)), (cx + 40, y0 + 190 + 240 * (1 - v)), (cx, y0 + 130 + 240 * (1 - v))], fill=alpha(RED, v))
            big_label(d, g, cx - tw(d, lab, F["h2"]) / 2, y0 + 440, lab, WHITE, v, "h2")
        if lt > 4:
            v = ease((lt - 4) / 0.6)
            rr(d, [x0 + 900, y0 + 120, x1 - 40, y0 + 460], 10, alpha(PANEL2, v), outline=alpha(GOLD, v * 0.6))
            d.text((x0 + 924, y0 + 140), "EXAMPLE · 20 OCT", font=F["tag"], fill=alpha(GOLD, v))
            d.text((x0 + 924, y0 + 180), "Headline: US & Iran", font=F["h3"], fill=alpha(WHITE, v))
            d.text((x0 + 924, y0 + 222), "\"close to agreement\"", font=F["h3"], fill=alpha(WHITE, v))
            big_label(d, g, x0 + 924, y0 + 280, "OIL −6%", RED, ease((lt - 6) / 0.5), "h2")
            d.text((x0 + 924, y0 + 350), "30 minutes later: Iran —", font=F["sm"], fill=alpha(MUTED, ease((lt - 8) / 0.5)))
            d.text((x0 + 924, y0 + 385), "\"no agreement\"", font=F["h3"], fill=alpha(GOLD, ease((lt - 8) / 0.5)))
        v = ease((lt - 11) / 0.6)
        d.text((x0 + 60, y1 - 80), "Expect headline attempts to control yields and oil short-term — they may not even be correct.", font=F["sm"], fill=alpha(MUTED, v))
        sx0, sy0, sx1, sy1 = side("WHAT TO DO")
        big_label(d, g, sx0 + 20, sy0 + 70, "BE READY FOR", WHITE, ease((lt - 12) / 0.5), "h2")
        big_label(d, g, sx0 + 20, sy0 + 125, "HEADLINE SHOCKS", RED, ease((lt - 12) / 0.5), "h2")
        d.text((sx0 + 20, sy0 + 210), "if yields or oil keep rising", font=F["sm"], fill=alpha(MUTED, ease((lt - 13) / 0.5)))
        caption(d, g, t); return True

    if p == 6:  # stocks: VIX up + Dow up
        topbar(d, g, t, u); ticker(d, t, u)
        x0, y0, x1, y1 = (40, 110, 1340, 870); rr(d, (x0, y0, x1, y1), 10, PANEL, outline=GRID2)
        d.text((x0 + 24, y0 + 16), "4 · THE STOCK MARKET  ·  VIX RISING WHILE THE DOW RISES", font=F["tag"], fill=MUTED)
        # two sparklines rising
        import random; random.seed(21)
        for i, (lab, col, at) in enumerate([("DOW", GREEN, 0.6), ("VIX", RED, 1.4)]):
            v = ease((lt - at) / 0.8); bx = x0 + 80 + i * 600; by = y0 + 120
            rr(d, [bx, by, bx + 520, by + 300], 8, PANEL2, outline=GRID2)
            d.text((bx + 16, by + 12), lab, font=F["h3"], fill=col)
            pts = []; yv = 0.35
            for k in range(40):
                yv += random.gauss(0.012, 0.03); yv = max(0.05, min(0.95, yv))
                pts.append((bx + 20 + k * 12, by + 280 - yv * 230))
            n = max(2, int(len(pts) * v)); d.line(pts[:n], fill=col, width=4); g.line(pts[:n], fill=mix((0, 0, 0), col, 0.5), width=10)
        stats = [("13–38 days per decade since 1995", "rare", 4.0), ("next 5 days: ±2.0–2.5% move", "mixed", 6.0), ("rise continued 54–68% of the time", "key", 8.0)]
        for i, (a, b, at) in enumerate(stats):
            v = ease((lt - at) / 0.5); yy = y0 + 460 + i * 60
            d.ellipse([x0 + 80, yy + 8, x0 + 100, yy + 28], fill=alpha(GOLD if i == 2 else DIM, v))
            d.text((x0 + 120, yy), a, font=F["h3"], fill=alpha(WHITE if i == 2 else MUTED, v))
        v = ease((lt - 12) / 0.6)
        d.text((x0 + 80, y1 - 70), "No crash soon → no margin calls → gold is not the first thing forced to be sold.", font=F["sm"], fill=alpha(GOLD, v))
        sx0, sy0, sx1, sy1 = side("WHY IT MATTERS FOR GOLD")
        chain = [("STOCKS HOLD UP", GREEN, 10), ("NO MARGIN CALLS", GREEN, 12), ("NO FORCED GOLD SELLING", GREEN, 14), ("NOVEMBER BOUNCE MORE LIKELY", GOLD, 16)]
        for i, (a, col, at) in enumerate(chain):
            v = ease((lt - at) / 0.5); yy = sy0 + 80 + i * 150
            rr(d, [sx0 + 20, yy, sx1 - 20, yy + 90], 8, alpha(PANEL2, v), outline=alpha(col, v * 0.7))
            d.text((sx0 + 36, yy + 28), a, font=F["h3"], fill=alpha(col, v))
            if i < 3: d.polygon([(sx0 + 250 - 14, yy + 100), (sx0 + 250 + 14, yy + 100), (sx0 + 250, yy + 130)], fill=alpha(DIM, v))
        caption(d, g, t); return True

    if p == 7:  # next put wall 4000 fut / 3980 spot: cushion
        topbar(d, g, t, u); ticker(d, t, u)
        px, py = chart(d, g, CHART_BOX, t, title="GOLD · 1H · THE NEXT WALL", level=True, level_u=1.0)
        if lt > 1.0: hline(py, L2, GOLD, "4,000 FUT ≈ 3,980 SPOT · PUT WALL · CUSHION", ease((lt - 1) / 0.6))
        if lt > 3:
            v = ease((lt - 3) / 0.8); lx, ly = px(N - 1), py(C[-1][3]); ex, ey = lx + 160 * v, py(L2) - 6
            d.line([(lx, ly), (lx + 160 * v, ly + (ey - ly) * v)], fill=alpha(RED, v), width=8); g.line([(lx, ly), (lx + 160 * v, ly + (ey - ly) * v)], fill=(110, 30, 30), width=18)
        if lt > 9:
            v = ease((lt - 9) / 0.8); yv = py(L2); xx = CHART_BOX[0] + 900
            d.line([(xx, yv - 10), (xx, yv - 10 - 140 * v)], fill=alpha(GREEN, v), width=10)
            d.polygon([(xx - 26, yv - 130 * v), (xx + 26, yv - 130 * v), (xx, yv - 170 * v)], fill=alpha(GREEN, v))
            d.text((xx - 420, yv - 200), "DROP INTO IT SLOWS / BOUNCES", font=F["h3"], fill=alpha(GREEN, v))
        x0, y0, x1, y1 = side("5 · PUT-HEAVY LEVEL · HOW IT BEHAVES")
        rows = [("PRICE BELOW IT", "only weak resistance above you", "→ that's why 4,150 gave way", RED, 4.5),
                ("PRICE ABOVE IT", "calm · puts sold for income · dealers long", "→ a drop into it slows or bounces: cushion", GREEN, 7.5)]
        for i, (h1, h2, h3, col, at) in enumerate(rows):
            v = ease((lt - at) / 0.5); yy = y0 + 70 + i * 220
            rr(d, [x0 + 20, yy, x1 - 20, yy + 190], 8, alpha(PANEL2, v), outline=alpha(col, v * 0.7))
            d.text((x0 + 36, yy + 16), h1, font=F["h3"], fill=alpha(col, v))
            d.text((x0 + 36, yy + 66), h2, font=F["sm"], fill=alpha(MUTED, v)); d.text((x0 + 36, yy + 110), h3, font=F["sm"], fill=alpha(WHITE, v))
        v = ease((lt - 13) / 0.6); big_label(d, g, x0 + 20, y1 - 150, "FINAL TP · 4,000–3,980", GOLD, v, "h3"); d.text((x0 + 20, y1 - 95), "then get ready for the other side", font=F["sm"], fill=alpha(MUTED, v))
        caption(d, g, t); return True

    if p == 8:  # the plan summary
        topbar(d, g, t, u); ticker(d, t, u)
        px, py = chart(d, g, (40, 110, 900, 870), t, title="GOLD · 1H", level=True, zoom_u=0.0)
        hline(py, L2, GOLD, "3,980 SPOT · PUT WALL", 1.0, 40, 900 - 120)
        x0, y0, x1, y1 = (930, 110, 1880, 870); rr(d, (x0, y0, x1, y1), 10, PANEL, outline=GRID2)
        d.text((x0 + 24, y0 + 16), "THE PLAN", font=F["tag"], fill=MUTED)
        rows = [("SCALE OUT SLOWLY", "final target 4,000 – 3,980 spot", GOLD, 1.0), ("WATCH THE BIG SHORTS", "do they cover? if not — squeeze fuel", WHITE, 3.5),
                ("EXPECT HEADLINE SHOCKS", "oil & yields", WHITE, 5.5), ("STOCKS HOLDING UP", "removes margin-call risk for gold", WHITE, 7.5),
                ("PUT WALL AT 4,000", "the cushion where the November bounce can start", GREEN, 9.5)]
        for i, (a, b, col, at) in enumerate(rows):
            v = ease((lt - at) / 0.5); yy = y0 + 70 + i * 140
            big_label(d, g, x0 + 30, yy - 6, str(i + 1), GOLD, v, "h1")
            d.text((x0 + 110, yy + 8), a, font=F["h3"], fill=alpha(col, v)); d.text((x0 + 110, yy + 52), b, font=F["body"], fill=alpha(MUTED, v))
        caption(d, g, t); return True

    return False
