import json, re
from pathlib import Path

test = Path(r'C:\Users\Tyler_AI\Desktop\test_scanner.html')
html = test.read_text(encoding='utf-8')

sb = re.search(r'font-weight:bold;color:#2ea043">(\d+)</span> <span style="color:#8b949e">Strong Buy', html)
wa = re.search(r'font-weight:bold;color:#58a6ff">(\d+)</span> <span style="color:#8b949e">Watch', html)
print('Counters: SB=' + (sb.group(1) if sb else 'N/A') + ', Watch=' + (wa.group(1) if wa else 'N/A'))

# Find embedded rowsData
idx = html.find('var rowsData=')
if idx < 0:
    print('NO rowsData found')
    exit()

arr_depth, end = 0, idx
for i in range(idx + 13, len(html)):
    if html[i] == '[': arr_depth += 1
    elif html[i] == ']':
        arr_depth -= 1
        if arr_depth == 0:
            end = i
            break

rows = json.loads(html[idx + 13:end + 1])
print('Stocks:', len(rows))
for s in rows:
    if s['ticker'] == 'MU':
        print('MU: $' + str(s['price']) + ', ' + str(s['days_left']) + 'd')
    if s['ticker'] == 'NOW':
        print('NOW: $' + str(s['price']) + ', ' + str(s['days_left']) + 'd')
