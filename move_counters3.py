c = open('ai_earnings_scanner.py', encoding='utf-8').read()

# Step 1: Remove old counter row (before How It Works button)
old1 = """html += '<div style="display:flex;gap:6px;align-items:center"><span style="background:#161b22;border:1px solid #2ea043;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#2ea043">' + str(strong_count) + '</span> <span style="color:#8b949e">Strong Buy</span></span><span style="background:#161b22;border:1px solid #1f6feb;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#58a6ff">' + str(sum(1 for s in stocks if round(s.composite_score) < 80)) + '</span> <span style="color:#8b949e">Watch</span></span></div>'"""
new1 = ""

if old1 in c:
    c = c.replace(old1, new1)
    print('Removed old counter row')
else:
    print('Old counter row not found')

# Step 2: Add counters below Run Scan button
old2 = "html += \"<button class=btn id=scanBtn onclick=runScan()>Run Scan</button>\"\n    html += '</div></div></div>'"
new2 = """html += \"<button class=btn id=scanBtn onclick=runScan()>Run Scan</button>\"
    html += '</div><div style="display:flex;gap:6px;align-items:center;margin-top:6px"><span style="background:#161b22;border:1px solid #2ea043;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#2ea043">' + str(strong_count) + '</span> <span style="color:#8b949e">Strong Buy</span></span><span style="background:#161b22;border:1px solid #1f6feb;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#58a6ff">' + str(sum(1 for s in stocks if round(s.composite_score) < 80)) + '</span> <span style="color:#8b949e">Watch</span></span></div></div></div>'"""

if old2 in c:
    c = c.replace(old2, new2)
    print('Counters added below Run Scan')
else:
    print('Run Scan closing not found')

open('ai_earnings_scanner.py', 'w', encoding='utf-8').write(c)
import ast
try:
    ast.parse(c)
    print('Syntax OK')
except SyntaxError as e:
    print(f'Syntax Error at line {e.lineno}')