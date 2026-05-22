import re
c = open('ai_earnings_today.html', encoding='utf-8').read()
# Find rows with SB/Buy/Hold/Sell - pattern: analysts count td then colored tds
rows = re.findall(r'color:#00ff88">(\d+)</td><td style="color:#58a6ff">(\d+)</td><td style="color:#ffcc00">(\d+)</td><td style="color:#ff6b6b">(\d+)</td>', c)
print(f'Found {len(rows)} stock rows')
for sb, b, h, s in rows[:8]:
    total = int(sb) + int(b) + int(h) + int(s)
    print(f'  SB={sb} B={b} H={h} S={s} -> sum={total}')
print('Total analyst reports = SB + B + H + S for every stock')