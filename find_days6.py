c = open('ai_earnings_today.html', encoding='utf-8').read()
idx = c.find("days_left<=7")
print(repr(c[idx-30:idx+150]))