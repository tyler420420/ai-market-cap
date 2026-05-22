c = open('ai_earnings_scanner.py', encoding='utf-8').read()
idx = c.find('display:flex;gap:6px;align-items:center')
print(repr(c[idx:idx+500]))