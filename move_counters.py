c = open('ai_earnings_today.html', encoding='utf-8').read()

# Find and restructure: move counters below buttons
old = """<div style="display:flex;flex-direction:column;gap:8px;align-items:flex-end;margin-left:auto"><div style="display:flex;gap:6px;align-items:center"><span style="background:#161b22;border:1px solid #2ea043;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#2ea043">7</span> <span style="color:#8b949e">Strong Buy</span></span><span style="background:#161b22;border:1px solid #1f6feb;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#58a6ff">13</span> <span style="color:#8b949e">Watch</span></span></div><div style="display:flex;gap:6px;align-items:center"><a href="/about" class=btn style="background:#1a2a2a;border:1px solid #30363d;color:#fff;padding:10px 18px;border-radius:6px;font-size:0.9em;text-decoration:none;font-weight:normal;box-shadow:none">How It Works</a><button class=btn id=refreshBtn onclick=refreshData()>Refresh</button><button class=btn id=scanBtn onclick=runScan()>Run Scan</button></div></div></div>"""

new = """<div style="display:flex;flex-direction:column;gap:8px;align-items:flex-end;margin-left:auto"><div style="display:flex;gap:6px;align-items:center"><a href="/about" class=btn style="background:#1a2a2a;border:1px solid #30363d;color:#fff;padding:10px 18px;border-radius:6px;font-size:0.9em;text-decoration:none;font-weight:normal;box-shadow:none">How It Works</a><button class=btn id=refreshBtn onclick=refreshData()>Refresh</button><button class=btn id=scanBtn onclick=runScan()>Run Scan</button></div><div style="display:flex;gap:6px;align-items:center;margin-top:4px"><span style="background:#161b22;border:1px solid #2ea043;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#2ea043">7</span> <span style="color:#8b949e">Strong Buy</span></span><span style="background:#161b22;border:1px solid #1f6feb;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#58a6ff">13</span> <span style="color:#8b949e">Watch</span></span></div></div></div>"""

if old in c:
    c = c.replace(old, new)
    open('ai_earnings_today.html', 'w', encoding='utf-8').write(c)
    print('Counters moved below buttons')
else:
    print('NOT found')