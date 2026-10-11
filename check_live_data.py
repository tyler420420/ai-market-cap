import urllib.request, re, json

# Try to get scanner_data.json
try:
    req = urllib.request.Request('https://aismarketcap.com/data',
        headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = r.read().decode('utf-8', errors='replace')
    parsed = json.loads(data)
    if isinstance(parsed, list) and parsed:
        first = parsed[0]
        print('Data stocks:', len(parsed))
        print('First stock:', first.get('ticker'), 'days_left:', first.get('days_left'))
        print('Sample:', parsed[:3])
    elif isinstance(parsed, dict):
        print('Dict keys:', list(parsed.keys())[:10])
except Exception as e:
    print('Data fetch error:', e)
