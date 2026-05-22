import urllib.request, re
# Test /cron with the same User-Agent and wait for completion
req = urllib.request.Request('https://aismarketcap.com/cron', headers={'User-Agent': 'Mozilla/5.0'})
try:
    resp = urllib.request.urlopen(req, timeout=120)
    body = resp.read().decode()
    print('Cron response:', body)
    print('Status:', resp.status)
except Exception as e:
    print('Error:', e)

# Now check homepage
import time
time.sleep(5)
req2 = urllib.request.Request('https://aismarketcap.com/', headers={'User-Agent': 'Mozilla/5.0'})
resp2 = urllib.request.urlopen(req2, timeout=15)
body2 = resp2.read().decode()
m = re.search(r'Updated.*?(\d{4}-\d{2}-\d{2})', body2)
print('Homepage Updated:', m.group(1) if m else 'none')
print('Serving ai_earnings_today:', 'ai_earnings_today' in body2)