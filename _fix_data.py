import urllib.request, json

url = 'https://aismarketcap.com/data'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=10) as resp:
    data = json.loads(resp.read())

# Save to local scanner_data.json
with open('scanner_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)

print(f'Downloaded {len(data)} stocks from live site')
for r in data:
    print(f'  {r["ticker"]} - {r["company_name"][:40]} - score {r["score"]}')
