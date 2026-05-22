c = open('ai_earnings_today.html', encoding='utf-8').read()

old = '<div style="display:flex;align-items:center;justify-content:center;text-align:center;padding:0 20px"><div style="background:#0d1520;border:1px solid #ffd700;border-radius:8px;padding:8px 16px;min-width:180px"><div style="color:#ffd700;font-size:0.75em;font-weight:bold;margin-bottom:2px">&#128293; TOP IPO</div><div id=ipo-main style="color:#58a6ff;font-size:1em;font-weight:bold">SpaceX</div><div style="color:#8b949e;font-size:0.72em">Aerospace | $1.5T | Late 2026</div></div></div><div style="display:flex;flex-direction:column;gap:8px;align-items:flex-end;margin-left:auto">'

new = '<div style="display:flex;align-items:center;justify-content:center;text-align:center;padding:0 15px;gap:12px"><div style="background:#0d1520;border:1px solid #ffd700;border-radius:8px;padding:8px 14px;min-width:150px"><div style="color:#ffd700;font-size:0.7em;font-weight:bold;margin-bottom:2px">&#128293; TOP IPO</div><div style="color:#58a6ff;font-size:0.95em;font-weight:bold">SpaceX</div><div style="color:#8b949e;font-size:0.68em">Aerospace | $1.5T</div></div><div style="background:#0d1520;border:1px solid #ffd700;border-radius:8px;padding:8px 14px;min-width:150px"><div style="color:#ffd700;font-size:0.7em;font-weight:bold;margin-bottom:2px">&#128293; TOP IPO</div><div style="color:#58a6ff;font-size:0.95em;font-weight:bold">OpenAI</div><div style="color:#8b949e;font-size:0.68em">AI | $1T</div></div><div style="background:#0d1520;border:1px solid #ffd700;border-radius:8px;padding:8px 14px;min-width:150px"><div style="color:#ffd700;font-size:0.7em;font-weight:bold;margin-bottom:2px">&#128293; TOP IPO</div><div style="color:#58a6ff;font-size:0.95em;font-weight:bold">Anthropic</div><div style="color:#8b949e;font-size:0.68em">AI | $300B</div></div></div><div style="display:flex;flex-direction:column;gap:8px;align-items:flex-end;margin-left:auto">'

if old in c:
    c = c.replace(old, new)
    open('ai_earnings_today.html', 'w', encoding='utf-8').write(c)
    print('3 IPO boxes added')
else:
    print('NOT found')