c = open('ai_earnings_today.html', encoding='utf-8').read()
idx = c.find('Strong Buy')
print(c[idx-500:idx+200])