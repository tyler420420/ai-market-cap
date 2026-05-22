c = open('ai_earnings_today.html', encoding='utf-8').read()

# Fix: remove the malformed div and duplicate header section
old = '<div id=ipo-main style="color:#58a6ff;font-size:1em;font-weight:bold">SpaceX</div><div style="color:#8b949e;font-size:0.72em">Aerospace | $1.5T | Late 2026</div></div></div><div style="display:flex style="color:#58a6ff;text-decoration:none"><h1>AI Market Cap Scanner</h1></a><div class=desc>Pre-earnings momentum scanner for Tech sector</div></div><div style="display:flex;flex-direction'
new = '<div id=ipo-main style="color:#58a6ff;font-size:1em;font-weight:bold">SpaceX</div><div style="color:#8b949e;font-size:0.72em">Aerospace | $1.5T | Late 2026</div></div></div><div style="display:flex;flex-direction'

if old in c:
    c = c.replace(old, new)
    open('ai_earnings_today.html', 'w', encoding='utf-8').write(c)
    print('Fixed')
else:
    print('NOT found - checking raw')
    idx = c.find('display:flex style')
    print(repr(c[idx:idx+200]))