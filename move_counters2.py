c = open('ai_earnings_today.html', encoding='utf-8').read()

# Step 1: Remove counters from their current spot (between IPO boxes and buttons)
old = """<span style="font-weight:bold;color:#2ea043">7</span> <span style="color:#8b949e">Strong Buy</span></span><span style="background:#161b22;border:1px solid #1f6feb;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#58a6ff">13</span> <span style="color:#8b949e">Watch</span></span></div><div style="display:flex;gap:6px;align-items:center"><a href="/about"""

new = """<a href="/about"""

if old in c:
    c = c.replace(old, new)
    print('Step 1: counters removed from top row')
else:
    print('Step 1: NOT found')

# Step 2: Add counters below buttons (after Run Scan button closes)
old2 = """onclick=runScan()>Run Scan</button></div></div></div><div class=warn"""
new2 = """onclick=runScan()>Run Scan</button></div><div style="display:flex;gap:6px;align-items:center;margin-top:6px"><span style="background:#161b22;border:1px solid #2ea043;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#2ea043">7</span> <span style="color:#8b949e">Strong Buy</span></span><span style="background:#161b22;border:1px solid #1f6feb;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#58a6ff">13</span> <span style="color:#8b949e">Watch</span></span></div></div></div><div class=warn"""

if old2 in c:
    c = c.replace(old2, new2)
    print('Step 2: counters added below buttons')
else:
    print('Step 2: NOT found')

open('ai_earnings_today.html', 'w', encoding='utf-8').write(c)
print('Done')