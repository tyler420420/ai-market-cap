c = open('ai_earnings_today.html', encoding='utf-8').read()
idx = c.find('Watch</span></span><a href')
print(repr(c[idx:idx+300]))