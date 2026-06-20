import urllib.request, re
req = urllib.request.Request('https://aismarketcap.com', headers={'User-Agent': 'Mozilla/5.0'})
r = urllib.request.urlopen(req)
html = r.read().decode('utf-8')

# Check counter values
sb = re.search(r'font-weight:bold;color:#2ea043">(\d+)</span> <span style="color:#8b949e">Strong Buy', html)
wa = re.search(r'font-weight:bold;color:#58a6ff">(\d+)</span> <span style="color:#8b949e">Watch', html)
print('LIVE: SB counter =', sb.group(1) if sb else 'NOT FOUND')
print('LIVE: Watch counter =', wa.group(1) if wa else 'NOT FOUND')

# Check rowsData first ticker
idx = html.find('var rowsData=')
rows = html[idx:idx+200]
print('rowsData start:', rows[:100])
