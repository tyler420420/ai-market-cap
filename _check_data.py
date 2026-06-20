import json
with open('scanner_data.json', encoding='utf-8') as f:
    data = json.load(f)
print(f'Stocks: {len(data)}')
for r in data[:5]:
    print(f'  {r["ticker"]} - {r["company_name"]} - score {r["score"]}')
