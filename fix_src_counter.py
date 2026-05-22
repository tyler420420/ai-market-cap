c = open('ai_earnings_scanner.py', encoding='utf-8').read()

# The old counter row is on two lines - remove it
old = """html += '<div style="display:flex;gap:6px;align-items:center">'
    html += '<span style="background:#161b22;border:1px solid #2ea043;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#2ea043">' + str(strong_count) + '</span> <span style="color:#8b949e">Strong Buy</span></span><span style="background:#161b22;border:1px solid #1f6feb;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#58a6ff">' + str(sum(1 for s in stocks if round(s.composite_score) < 80)) + '</span> <span style="color:#8b949e">Watch</span></span></div>'"""
new = ""

if old in c:
    c = c.replace(old, new)
    print('Removed old counter row')
else:
    print('Not found')