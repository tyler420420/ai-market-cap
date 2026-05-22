c = open('ai_earnings_today.html', encoding='utf-8').read()
# Find the days_left cell in table render - look for d+'d' which renders the days number
idx = c.find("d+'d'")
print(c[idx-100:idx+200])