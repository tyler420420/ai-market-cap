c = open('ai_earnings_today.html', encoding='utf-8').read()
idx = c.find('display:flex;gap:6px;align-items:center')
print(repr(c[idx-20:idx+500]))