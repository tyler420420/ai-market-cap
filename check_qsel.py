with open('ai_earnings_57day_20260520_0153.html', 'r', encoding='utf-8') as f:
    c = f.read()
idx = c.find("querySelector('th[data-col=")
print('Found at:', idx)
if idx >= 0:
    with open('qsel.txt', 'w', encoding='utf-8') as out:
        out.write(c[idx:idx+60])
    print('Written')