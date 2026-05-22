c = open('ai_earnings_today.html', encoding='utf-8').read()
idx = c.find('body{')
print(repr(c[idx:idx+80]))