import urllib.request, re

# Check what Railway container is actually running by hitting the cron endpoint
# The new code would log specific messages if it patched scanner.html
# Old code just says "Scan triggered" and doesn't have the patch

req = urllib.request.Request(
    'https://aismarketcap.com/cron?force=1',
    headers={'User-Agent': 'Railway/1.0 CronJob'}
)
try:
    r = urllib.request.urlopen(req, timeout=10)
    body = r.read(500).decode('utf-8')
    print('HTTP status:', r.status)
    print('Response body:', body)
except Exception as e:
    print('Error:', e)
