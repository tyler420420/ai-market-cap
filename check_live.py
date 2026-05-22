import urllib.request, re
req = urllib.request.Request('https://aismarketcap.com/', headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, timeout=15)
body = resp.read().decode()
scripts = re.findall(r'ai_earnings_[^"]+\.html', body)
print('HTML files referenced:', scripts[:5])
m = re.search(r'Scan Date.*?(\d{4}-\d{2}-\d{2} \d{2}:\d{2})', body)
if m: print('Scan date:', m.group(1))
m = re.search(r'Updated.*?(\d{4}-\d{2}-\d{2})', body)
if m: print('Updated:', m.group(1))
# check if it's ai_earnings_today or fallback
if 'ai_earnings_today' in body:
    print('Serving from ai_earnings_today.html')
else:
    print('Serving from fallback (dated file)')
    dated = re.findall(r'ai_earnings_\d+_\d+\.html', body)
    print('Dated file:', dated[:2] if dated else 'none found')