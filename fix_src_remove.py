c = open('ai_earnings_scanner.py', encoding='utf-8').read()

# Remove lines 439-441 (old counter row before buttons)
old = """html += '<div style="display:flex;gap:6px;align-items:center">'
    html += '<span style="background:#161b22;border:1px solid #2ea043;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#2ea043">' + str(strong_count) + '</span> <span style="color:#8b949e">Strong Buy</span></span>'
    html += '<span style="background:#161b22;border:1px solid #1f6feb;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#58a6ff">' + str(sum(1 for s in stocks if round(s.composite_score) < 80)) + '</span> <span style="color:#8b949e">Watch</span></span>'
    html += '<a href="/about" class=btn style="background:#1a2a2a;border:1px solid #30363d;color:#fff;padding:10px 18px;border-radius:6px;font-size:0.9em;text-decoration:none;font-weight:normal;box-shadow:none">How It Works</a>'"""

new = """html += '<div style="display:flex;gap:6px;align-items:center">'
    html += '<a href="/about" class=btn style="background:#1a2a2a;border:1px solid #30363d;color:#fff;padding:10px 18px;border-radius:6px;font-size:0.9em;text-decoration:none;font-weight:normal;box-shadow:none">How It Works</a>'"""

if old in c:
    c = c.replace(old, new)
    print('Old counter row removed from source')
else:
    print('Not found - trying different approach')
    # Find and remove just the two counter lines
    old2 = """html += '<span style="background:#161b22;border:1px solid #2ea043;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#2ea043">' + str(strong_count) + '</span> <span style="color:#8b949e">Strong Buy</span></span>'"""
    old3 = """html += '<span style="background:#161b22;border:1px solid #1f6feb;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#58a6ff">' + str(sum(1 for s in stocks if round(s.composite_score) < 80)) + '</span> <span style="color:#8b949e">Watch</span></span>'"""
    
    if old2 in c:
        c = c.replace(old2, '')
        print('Removed first counter line')
    if old3 in c:
        c = c.replace(old3, '')
        print('Removed second counter line')

open('ai_earnings_scanner.py', 'w', encoding='utf-8').write(c)
import ast
try:
    ast.parse(c)
    print('Syntax OK')
except SyntaxError as e:
    print(f'Syntax Error at line {e.lineno}')