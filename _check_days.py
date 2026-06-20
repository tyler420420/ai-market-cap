import re

with open('ai_earnings_today.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Check days_color function
m = re.search(r'function days_color\([^)]+\)\{return[^}]+\}', html)
if m:
    print('days_color function:', m.group(0))

# Check static rows for days colors
rows = re.findall(r'data-label="Days"><span style="color:([^"]+)">(\d+)</span>', html)
from collections import Counter
print('\nStatic rows days color distribution:')
for (color, days), count in sorted(Counter(rows).items()):
    print(f'  {color} (days {days}): {count}')

# Check JS rows_data for days colors
js = re.search(r'rowsData=(\[.*?\]);', html, re.DOTALL)
if js:
    js_data = js.group(1)
    green = js_data.count('#00ff88')
    blue = js_data.count('#58a6ff')
    yellow = js_data.count('#ffcc00')
    red = js_data.count('#ff4444')
    print(f'\nJS rowsData days color mentions:')
    print(f'  green #00ff88: {green}')
    print(f'  blue #58a6ff: {blue}')
    print(f'  yellow #ffcc00: {yellow}')
    print(f'  red #ff4444: {red}')
