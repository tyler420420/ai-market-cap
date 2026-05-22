import re

with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Find and replace the squeeze badge in renderTable
old = "html+='<td>'+(r.squeeze?'<span style=\"background:#1a0a0a;border:1px solid #ff4444;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#ff6b6b\">SQUEEZE</span>':'—')+'</td>'"
new = "html+='<td>'+(r.squeeze?'<span style=\"background:#1a2a1a;border:1px solid #2ea043;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#00ff88\">SHORT</span>':'—')+'</td>'"

if old in c:
    c = c.replace(old, new)
    print('Done')
else:
    # Try with escaped quotes
    old2 = "html+=\'<td>\'+(r.squeeze?\'<span style=\\\'background:#1a0a0a;border:1px solid #ff4444;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#ff6b6b\\'>SQUEEZE</span>\':\'—\')+\'</td>\'"
    print(f'Old2 in file: {old2 in c}')
    # Search for it
    idx = c.find('SQUEEZE')
    if idx >= 0:
        print(f'Found SQUEEZE at {idx}')
        print(repr(c[idx-50:idx+150]))

with open('ai_earnings_scanner.py', 'w', encoding='utf-8') as f:
    f.write(c)