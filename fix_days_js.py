path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'rb') as f:
    content = f.read()

old = b"html+='<td style=\\\"color:\\'+(r.days_left==0?\\'#ff4444\\':(r.days_left<=7?\\'#00ff88\\':\\'#ffcc00\\'))+\\\";font-weight:bold\\'>\\'+(r.days_left==0?\\'Today\\':r.days_left+\\'d\\')+\\'</td>"
new = b"html+='<td style=\\\"color:\\'+(r.days_left==0?\\'#ff4444\\':(r.days_left<=14?\\'#ffcc00\\':(r.days_left<=35?\\'#58a6ff\\':\\'#00ff88\\'))+\\\";font-weight:bold\\'>\\'+(r.days_left==0?\\'Today\\':r.days_left+\\'d\\')+\\'</td>"

if old in content:
    content = content.replace(old, new)
    with open(path, 'wb') as f:
        f.write(content)
    print('OK')
else:
    print('MISS')
    # dump actual
    idx = content.find(b"html+='<td style")
    print(repr(content[idx:idx+200]))