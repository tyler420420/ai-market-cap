c = open('ai_earnings_today.html', encoding='utf-8').read()
old = '<div class=header><div class=hdr-row><div><a href="https://aismarketcap.com"'
new = """<div class=header><div class=hdr-row><div><a href="https://aismarketcap.com" style="color:#58a6ff;text-decoration:none"><h1>AI Market Cap Scanner</h1></a><div class=desc>Pre-earnings momentum scanner for Tech sector</div></div><div style="display:flex;align-items:center;justify-content:center;text-align:center;padding:0 20px"><div style="background:#0d1520;border:1px solid #ffd700;border-radius:8px;padding:8px 16px;min-width:180px"><div style="color:#ffd700;font-size:0.75em;font-weight:bold;margin-bottom:2px">&#128293; TOP IPO</div><div id=ipo-main style="color:#58a6ff;font-size:1em;font-weight:bold">SpaceX</div><div style="color:#8b949e;font-size:0.72em">Aerospace | $1.5T | Late 2026</div></div></div><div style="display:flex"""
if old in c:
    c = c.replace(old, new)
    open('ai_earnings_today.html', 'w', encoding='utf-8').write(c)
    print('IPO section added')
else:
    print('NOT found')