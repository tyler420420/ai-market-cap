c = open('ai_earnings_today.html', encoding='utf-8').read()
# Find days_left rendered as 'd' - look for days_left coloring
idx = c.find("days_left<=7")
print(c[idx-50:idx+200])