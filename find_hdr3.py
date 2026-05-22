c = open('ai_earnings_today.html', encoding='utf-8').read()
idx = c.find('class=header')
print(c[idx:idx+500])