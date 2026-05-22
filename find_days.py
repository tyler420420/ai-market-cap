c = open('ai_earnings_today.html', encoding='utf-8').read()
idx = c.find("days_left'")
print(c[idx-80:idx+120])