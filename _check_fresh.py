import urllib.request, json
req = urllib.request.Request('https://aismarketcap.com/data', headers={'User-Agent': 'Mozilla/5.0'})
r = urllib.request.urlopen(req)
data = json.loads(r.read())
print('Stocks:', len(data))
for s in data[:5]:
    print('  ' + s['ticker'] + ': $' + str(s['price']) + ', ' + str(s['days_left']) + 'd, ' + s['earnings_date'])
for s in data:
    if s['ticker'] == 'MU':
        print('MU: $' + str(s['price']) + ', ' + str(s['days_left']) + 'd, ' + s['earnings_date'])
        break
