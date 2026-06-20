from pathlib import Path
import json, re

html = Path('ai_earnings_today.html').read_text(encoding='utf-8')
idx = html.find('var rowsData=')
arr_depth, end = 0, idx
for i in range(idx + 13, len(html)):
    if html[i] == '[': arr_depth += 1
    elif html[i] == ']':
        arr_depth -= 1
        if arr_depth == 0: end = i; break
rows = json.loads(html[idx + 13:end + 1])

print('Top 5 stocks:')
for s in rows[:5]:
    print('  ' + s['ticker'] + ': score=' + str(s['score']) + ', price=$' + str(s['price']) + ', ' + str(s['days_left']) + 'd, ' + s['earnings_date'])
