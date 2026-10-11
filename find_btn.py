content = open(r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_today.html', 'r', encoding='utf-8').read()
idx = content.find('FAQ')
print('FAQ at:', idx)
if idx > 0:
    print(repr(content[max(0,idx-250):idx+100]))
