import urllib.request, re, time

print('Triggering cron (force=1)...')
req = urllib.request.Request('https://aismarketcap.com/cron?force=1', headers={'User-Agent': 'Railway/1.0 CronJob'})
r = urllib.request.urlopen(req, timeout=5)
print('Immediate response:', r.read(50))
print('Waiting 95s for scan to complete...')
time.sleep(95)
print('Done waiting. Checking live site...')

req2 = urllib.request.Request('https://aismarketcap.com', headers={'User-Agent': 'Mozilla/5.0'})
r2 = urllib.request.urlopen(req2)
html = r2.read().decode('utf-8')

# Check counter
sb = re.search(r'font-weight:bold;color:#2ea043">(\d+)</span>', html)
wa = re.search(r'font-weight:bold;color:#58a6ff">(\d+)</span>', html)
print('SB counter:', sb.group(1) if sb else 'NOT FOUND')
print('Watch counter:', wa.group(1) if wa else 'NOT FOUND')

# Check rowsData embedded in site
idx = html.find('var rowsData=')
if idx >= 0:
    snippet = html[idx:idx+100]
    print('rowsData snippet:', snippet[:80])
else:
    print('NO rowsData found in main page!')

# Check data endpoint too
req3 = urllib.request.Request('https://aismarketcap.com/data', headers={'User-Agent': 'Mozilla/5.0'})
r3 = urllib.request.urlopen(req3)
import json
data = json.loads(r3.read())
print('/data endpoint has', len(data), 'stocks')
for s in data[:3]:
    print('  ' + s['ticker'] + ': $' + str(s['price']) + ', ' + str(s['days_left']) + 'd')
