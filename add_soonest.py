c = open('ai_earnings_today.html', encoding='utf-8').read()

old = '<div style="display:flex;align-items:center;justify-content:center;text-align:center;padding:0 15px;gap:12px"><div style="background:#0d1520;border:1px solid #ffd700;border-radius:8px;padding:8px 14px;min-width:150px"><div style="color:#ffd700;font-size:0.7em;font-weight:bold;margin-bottom:2px">&#128293; TOP IPO</div><div style="color:#58a6ff;font-size:0.95em;font-weight:bold">SpaceX</div><div style="color:#8b949e;font-size:0.68em">Aerospace | $1.5T | Late 2026</div></div>'

new = '<div style="display:flex;align-items:center;justify-content:center;text-align:center;padding:0 15px;gap:12px"><div style="background:#0d1a0d;border:1px solid #2ea043;border-radius:8px;padding:8px 14px;min-width:150px;box-shadow:0 0 10px rgba(46,160,67,0.3)"><div style="color:#2ea043;font-size:0.65em;font-weight:bold;margin-bottom:2px">&#128293; SOONEST IPO</div><div style="color:#00ff88;font-size:0.95em;font-weight:bold">Monzo</div><div style="color:#8b949e;font-size:0.68em">Fintech | $8B | Q2 2026</div></div><div style="background:#0d1520;border:1px solid #ffd700;border-radius:8px;padding:8px 14px;min-width:150px"><div style="color:#ffd700;font-size:0.7em;font-weight:bold;margin-bottom:2px">&#128293; TOP IPO</div><div style="color:#58a6ff;font-size:0.95em;font-weight:bold">SpaceX</div><div style="color:#8b949e;font-size:0.68em">Aerospace | $1.5T | Late 2026</div></div>'

if old in c:
    c = c.replace(old, new)
    open('ai_earnings_today.html', 'w', encoding='utf-8').write(c)
    print('Soonest IPO added first')
else:
    print('NOT found')