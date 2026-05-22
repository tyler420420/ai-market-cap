c = open('ai_earnings_today.html', encoding='utf-8').read()

# First occurrence (index 18309) is the OLD duplicate - leads to "How It Works" link
# Second occurrence (index 19159) is the NEW one below buttons - leads to closing divs

# Find the first one and remove the entire counter div that precedes it
# Pattern: the old duplicate is right before "How It Works" link

old = """<span style="background:#161b22;border:1px solid #2ea043;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#2ea043">7</span> <span style="color:#8b949e">Strong Buy</span></span><span style="background:#161b22;border:1px solid #1f6feb;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#58a6ff">13</span> <span style="color:#8b949e">Watch</span></span><a href="/about\""""

new = """<a href="/about\""""

if old in c:
    c = c.replace(old, new)
    open('ai_earnings_today.html', 'w', encoding='utf-8').write(c)
    print('Old duplicate removed')
else:
    print('NOT found')