import urllib.request, re

req = urllib.request.Request('https://aismarketcap.com', headers={'User-Agent': 'Mozilla/5.0'})
r = urllib.request.urlopen(req)
live = r.read().decode('utf-8')

# Find all ticker links
tickers = re.findall(r'/quote/([A-Z]+)', live)
# Deduplicate while preserving order
seen = set()
unique_tickers = []
for t in tickers:
    if t not in seen:
        seen.add(t)
        unique_tickers.append(t)
print('Tickers:', unique_tickers[:15])

# Find days left values
days = re.findall(r'font-weight:bold">(\d+d)</span>', live)
print('Days left:', days[:15])

# Check what the local file has
with open('ai_earnings_today.html', 'r', encoding='utf-8') as f:
    local = f.read()
local_tickers = re.findall(r'/quote/([A-Z]+)', local)
seen2 = set()
unique_local = []
for t in local_tickers:
    if t not in seen2:
        seen2.add(t)
        unique_local.append(t)
print('LOCAL tickers:', unique_local[:15])
local_days = re.findall(r'font-weight:bold">(\d+d)</span>', local)
print('LOCAL days:', local_days[:15])
