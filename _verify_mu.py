import urllib.request, re

req = urllib.request.Request('https://aismarketcap.com', headers={'User-Agent': 'Mozilla/5.0', 'Cache-Control': 'no-cache'})
html = urllib.request.urlopen(req).read().decode('utf-8')

# Find embedded rowsData and extract MU
import json
idx = html.find('var rowsData=')
if idx >= 0:
    arr_depth, end = 0, idx
    for i in range(idx + 13, len(html)):
        if html[i] == '[': arr_depth += 1
        elif html[i] == ']':
            arr_depth -= 1
            if arr_depth == 0:
                end = i
                break
    rows = json.loads(html[idx + 13:end + 1])
    print('Total stocks:', len(rows))
    for s in rows:
        if s['ticker'] == 'MU':
            print('MU: $' + str(s['price']) + ', ' + str(s['days_left']) + 'd, earnings=' + s['earnings_date'])
        if s['ticker'] == 'NOW':
            print('NOW: $' + str(s['price']) + ', ' + str(s['days_left']) + 'd')
else:
    print('No rowsData found')
