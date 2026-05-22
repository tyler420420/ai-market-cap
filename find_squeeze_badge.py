with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    c = f.read()

idx = c.find('SHORT</span>')
if idx >= 0:
    print(repr(c[idx-50:idx+80]))
else:
    print('SHORT not found')

idx2 = c.find('Short</span>')
if idx2 >= 0:
    print(repr(c[idx2-50:idx2+80]))