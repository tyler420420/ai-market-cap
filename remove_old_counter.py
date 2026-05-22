c = open('ai_earnings_today.html', encoding='utf-8').read()

# Find first Watch</span></span> and remove the counter row before it
# This is the old duplicate before How It Works button
idx = c.find('Watch</span></span><a href="/about"')
print(f'Found old counter at: {idx}')

# Remove the entire counter row that precedes this - it's the span before Watch
# The pattern is: <span...>7</span> <span...>Strong Buy</span></span><span...>13</span> <span...>Watch</span></span>
old = '<span style="background:#161b22;border:1px solid #2ea043;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#2ea043">7</span> <span style="color:#8b949e">Strong Buy</span></span><span style="background:#161b22;border:1px solid #1f6feb;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#58a6ff">13</span> <span style="color:#8b949e">Watch</span></span><a href="/about"'

if old in c:
    c = c.replace(old, '<a href="/about"')
    open('ai_earnings_today.html', 'w', encoding='utf-8').write(c)
    print('Removed old duplicate before How It Works')
else:
    print('Pattern not found - trying simpler approach')
    # Try to find and remove just the counter row before How It Works
    idx = c.find('Watch</span></span><a href="/about"')
    if idx > 0:
        # Find where this section starts (go back to find the opening div of this counter row)
        start = c.rfind('<div style="display:flex;gap:6px;align-items:center">', 0, idx)
        if start >= 0:
            end = idx + len('Watch</span></span>')
            c = c[:start] + c[end:]
            open('ai_earnings_today.html', 'w', encoding='utf-8').write(c)
            print(f'Removed from {start} to {end}')
        else:
            print('Could not find start of section')