c = open('ai_earnings_today.html', encoding='utf-8').read()
idx = c.find("days_left")
print(repr(c[idx-20:idx+80]))