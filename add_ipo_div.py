c = open('ai_earnings_scanner.py', encoding='utf-8').read()

# Add IPO ticker after the header closing divs (after header ends and before ticker strip)
# Find: after the header div closes but before ticker strip
old = "html += '<div class=ticker-strip><div class=ticker-strip-inner>' + ticker_items + ticker_items + '</div></div>'"
new = """html += '<div id=ipo-ticker style="background:#0d1520;border:1px solid #30363d;border-radius:8px;padding:10px 18px;margin:15px 0;font-size:0.85em;text-align:center"><span style="color:#ffd700;font-weight:bold">&#128293; IPO Watch:</span> <span id=ipo-name style="color:#58a6ff;font-weight:bold"></span> <span id=ipo-detail style="color:#8b949e"></span></div>'
    html += '<div class=ticker-strip><div class=ticker-strip-inner>' + ticker_items + ticker_items + '</div></div>'"""

if old in c:
    c = c.replace(old, new)
    open('ai_earnings_scanner.py', 'w', encoding='utf-8').write(c)
    print('IPO ticker div added')
else:
    print('NOT found')