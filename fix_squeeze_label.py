with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    c = f.read()

old = "html+=\'<td>\'+(r.squeeze?\'<span style=\\\'background:#1a2a1a;border:1px solid #2ea043;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#00ff88\\\'>SHORT</span>\':\'—\')+\'</td>\'"
new = "html+=\'<td>\'+(r.squeeze?\'<span style=\\\'background:#1a2a1a;border:1px solid #2ea043;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#00ff88\\\'>Squeeze</span>\':\'—\')+\'</td>\'"

if old in c:
    c = c.replace(old, new)
    print('Done')
else:
    print('FAILED')

with open('ai_earnings_scanner.py', 'w', encoding='utf-8') as f:
    f.write(c)