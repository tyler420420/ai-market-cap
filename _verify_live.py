import urllib.request, re, json

req = urllib.request.Request('https://aismarketcap.com', headers={'User-Agent': 'Mozilla/5.0'})
html = urllib.request.urlopen(req).read().decode('utf-8')

sb = re.search(r'font-weight:bold;color:#2ea043">(\d+)</span> <span style="color:#8b949e">Strong Buy', html)
wa = re.search(r'font-weight:bold;color:#58a6ff">(\d+)</span> <span style="color:#8b949e">Watch', html)
print('LIVE counters: SB=' + (sb.group(1) if sb else 'N/A') + ', Watch=' + (wa.group(1) if wa else 'N/A'))

# Find MU row
mu_idx = html.find('"ticker": "MU"')
if mu_idx >= 0:
    snippet = html[mu_idx-5:mu_idx+150]
    m = re.search(r'"price":\s*([0-9.]+).*?"days_left":\s*(\d+)', snippet)
    if m:
        print('MU: price=' + m.group(1) + ', days_left=' + m.group(2))
    else:
        print('MU row snippet:', snippet[:100])

# Check embedded rowsData
idx = html.find('var rowsData=')
if idx >= 0:
    m2 = re.search(r'"ticker": "([^"]+)".*?"price":\s*([0-9.]+)', html[idx:idx+500])
    if m2:
        print('First ticker: ' + m2.group(1) + ', price=' + m2.group(2))
else:
    print('NO embedded rowsData found!')
