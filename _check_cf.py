import urllib.request

# Check Cloudflare cache headers
req = urllib.request.Request('https://aismarketcap.com', headers={'User-Agent': 'Mozilla/5.0', 'Cache-Control': 'no-cache'})
r = urllib.request.urlopen(req)
print('CF-Cache-Status:', r.headers.get('cf-cache-status', 'N/A'))
print('Cache-Control:', r.headers.get('Cache-Control', 'N/A'))
print('Content-Length:', r.headers.get('Content-Length', 'N/A'))

# Check if this is the new scanner.html
html = r.read().decode('utf-8')
import re
sb = re.search(r'font-weight:bold;color:#2ea043">(\d+)</span> <span style="color:#8b949e">Strong Buy', html)
wa = re.search(r'font-weight:bold;color:#58a6ff">(\d+)</span> <span style="color:#8b949e">Watch', html)
print('Counters: SB=' + (sb.group(1) if sb else 'N/A') + ', Watch=' + (wa.group(1) if wa else 'N/A'))
