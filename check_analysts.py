import re
c = open('ai_earnings_today.html', encoding='utf-8').read()
# Pattern: analyst count td followed by sb/buy/hold/sell tds
matches = re.findall(r'<td>(\d+)</td><td style="color:#00ff88">(\d+)</td><td style="color:#58a6ff">(\d+)</td><td style="color:#ffcc00">(\d+)</td><td style="color:#ff6b6b">(\d+)</td>', c)
print('Analyst Reports | S-BUY | Buy | Hold | Sell | Total | Check')
for m in matches[:10]:
    total = int(m[0])
    breakdown = int(m[1])+int(m[2])+int(m[3])+int(m[4])
    match = 'OK' if total == breakdown else f'MISMATCH (sum={breakdown})'
    print(f'{m[0]:>15} | {m[1]:>5} | {m[2]:>3} | {m[3]:>4} | {m[4]:>4} | ={breakdown} | {match}')