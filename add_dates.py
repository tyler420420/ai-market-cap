c = open('ai_earnings_today.html', encoding='utf-8').read()

old = """Aerospace | $1.5T</div></div><div style="background:#0d1520;border:1px solid #ffd700;border-radius:8px;padding:8px 14px;min-width:150px"><div style="color:#ffd700;font-size:0.7em;font-weight:bold;margin-bottom:2px">&#128293; TOP IPO</div><div style="color:#58a6ff;font-size:0.95em;font-weight:bold">OpenAI</div><div style="color:#8b949e;font-size:0.68em">AI | $1T</div></div><div style="background:#0d1520;border:1px solid #ffd700;border-radius:8px;padding:8px 14px;min-width:150px"><div style="color:#ffd700;font-size:0.7em;font-weight:bold;margin-bottom:2px">&#128293; TOP IPO</div><div style="color:#58a6ff;font-size:0.95em;font-weight:bold">Anthropic</div><div style="color:#8b949e;font-size:0.68em">AI | $300B</div></div>"""

new = """Aerospace | $1.5T | Late 2026</div></div><div style="background:#0d1520;border:1px solid #ffd700;border-radius:8px;padding:8px 14px;min-width:150px"><div style="color:#ffd700;font-size:0.7em;font-weight:bold;margin-bottom:2px">&#128293; TOP IPO</div><div style="color:#58a6ff;font-size:0.95em;font-weight:bold">OpenAI</div><div style="color:#8b949e;font-size:0.68em">AI | $1T | 2026-2027</div></div><div style="background:#0d1520;border:1px solid #ffd700;border-radius:8px;padding:8px 14px;min-width:150px"><div style="color:#ffd700;font-size:0.7em;font-weight:bold;margin-bottom:2px">&#128293; TOP IPO</div><div style="color:#58a6ff;font-size:0.95em;font-weight:bold">Anthropic</div><div style="color:#8b949e;font-size:0.68em">AI | $300B | Late 2026</div></div>"""

if old in c:
    c = c.replace(old, new)
    open('ai_earnings_today.html', 'w', encoding='utf-8').write(c)
    print('Dates added')
else:
    print('NOT found')