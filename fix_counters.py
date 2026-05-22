c = open('ai_earnings_today.html', encoding='utf-8').read()

# Find the section with counters and buttons and restructure
old = """<span style="font-weight:bold;color:#2ea043">7</span> <span style="color:#8b949e">Strong Buy</span></span><span style="background:#161b22;border:1px solid #1f6feb;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#58a6ff">13</span> <span style="color:#8b949e">Watch</span></span></div><div style="display:flex;gap:6px;align-items:center"><a href="/about" class=btn"""

new = """<a href="/about" class=btn"""

if old in c:
    c = c.replace(old, new)
    open('ai_earnings_today.html', 'w', encoding='utf-8').write(c)
    print('Step 1 done - removed old counter div')
else:
    print('NOT found')