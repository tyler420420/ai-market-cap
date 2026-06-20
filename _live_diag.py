import urllib.request, re, json

req = urllib.request.Request('https://aismarketcap.com', headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Cache-Control': 'no-cache'})
r = urllib.request.urlopen(req)
html = r.read().decode('utf-8')

print('Page length:', len(html))

# Find ALL occurrences of rowsData
idx = 0
count = 0
while True:
    idx = html.find('var rowsData=', idx)
    if idx < 0:
        break
    print('rowsData at:', idx)
    idx += 1
    count += 1
print('Total rowsData occurrences:', count)

# Check if it fetches from /data
print('Fetches /data?:', '/data' in html and 'fetch' in html)

# Try to parse embedded rowsData
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
    snippet = html[idx + 13:end + 1]
    print('Embedded data length:', len(snippet))
    try:
        data = json.loads(snippet)
        print('JSON OK,', len(data), 'stocks')
        print('First ticker:', data[0]['ticker'], '$' + str(data[0]['price']), str(data[0]['days_left']) + 'd')
        print('Last ticker:', data[-1]['ticker'], '$' + str(data[-1]['price']))
    except Exception as e:
        print('JSON error:', e)
        print('Snippet:', repr(snippet[:200]))
else:
    print('NO embedded rowsData!')
