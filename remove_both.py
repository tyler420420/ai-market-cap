c = open('ai_earnings_today.html', encoding='utf-8').read()

removed = 0

# Remove first counter section - appears before IPO boxes
# Pattern: ends with Watch</span></span> and leads to IPO boxes
old1 = '<span style="background:#161b22;border:1px solid #2ea043;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#2ea043">7</span> <span style="color:#8b949e">Strong Buy</span></span><span style="background:#161b22;border:1px solid #1f6feb;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#58a6ff">13</span> <span style="color:#8b949e">Watch</span></span></div><div style="display:flex;align-items:center;justify-content:center'
if old1 in c:
    c = c.replace(old1, '<div style="display:flex;align-items:center;justify-content:center')
    removed += 1
    print('Removed first counter section')

# Remove second counter section - appears before How It Works button
old2 = '<span style="background:#161b22;border:1px solid #2ea043;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#2ea043">7</span> <span style="color:#8b949e">Strong Buy</span></span><span style="background:#161b22;border:1px solid #1f6feb;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#58a6ff">13</span> <span style="color:#8b949e">Watch</span></span></div><div style="display:flex;gap:6px;align-items:center"><a href="/about"'
if old2 in c:
    c = c.replace(old2, '<div style="display:flex;gap:6px;align-items:center"><a href="/about"')
    removed += 1
    print('Removed second counter section')

print(f'Total removed: {removed}')

open('ai_earnings_today.html', 'w', encoding='utf-8').write(c)
print('Done')