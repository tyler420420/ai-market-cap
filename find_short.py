with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    c = f.read()

old = "html+='<td>\'+(r.squeeze?\'<span style=\\\'background:#1a2a1a;border:1px solid #2ea043;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#00ff88\\\'>SHORT</span>\':\'—\')+\'</td>\'"

print(f'Old in file: {old in c}')

# Find where it actually is
idx = c.find('SHORT</span>')
if idx >= 0:
    print(f'SHORT found at {idx}')
    print(repr(c[idx-100:idx+80]))
else:
    print('SHORT not found, checking for SQUEEZE')
    idx2 = c.find('SQUEEZE')
    if idx2 >= 0:
        print(f'SQUEEZE found at {idx2}')
        print(repr(c[idx2-100:idx2+80]))