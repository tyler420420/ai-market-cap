import re
f = open('C:/Users/Tyler_AI/ai-market-cap/ai_earnings_today.html', 'r', encoding='utf-8').read()
idx = f.find("AI's Suggested Trade")
if idx < 0:
    idx = f.find('Suggested Trade')
snippet = f[idx:idx+600]
print(snippet)
print('---')

# Also check what MU shows
idx2 = f.find('MU')
if idx2 > 0:
    # find days_left for MU
    snippet2 = f[idx2-200:idx2+300]
    print(snippet2)
