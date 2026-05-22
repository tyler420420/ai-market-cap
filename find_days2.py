c = open('ai_earnings_today.html', encoding='utf-8').read()
idx = c.find("r.days_left")
print(c[idx-100:idx+150])