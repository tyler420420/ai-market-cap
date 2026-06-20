import time, urllib.request, re
time.sleep(95)
req = urllib.request.Request('https://aismarketcap.com', headers={'User-Agent': 'Mozilla/5.0'})
html = urllib.request.urlopen(req).read().decode('utf-8')
sb = re.search(r'font-weight:bold;color:#2ea043">(\d+)</span>', html)
wa = re.search(r'font-weight:bold;color:#58a6ff">(\d+)</span>', html)
print('SB counter:', sb.group(1) if sb else 'NOT FOUND')
print('Watch counter:', wa.group(1) if wa else 'NOT FOUND')
idx = html.find('var rowsData=')
if idx >= 0:
    print('rowsData:', html[idx:idx+80])
else:
    print('rowsData: NOT FOUND in main page')
