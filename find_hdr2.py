c = open('ai_earnings_today.html', encoding='utf-8').read()
idx = c.find('hdr-row')
print(c[idx-200:idx+100])