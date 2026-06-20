import json
with open('scanner_data.json', encoding='utf-8') as f:
    data = json.load(f)
# Check for IPO/DRAM rows
for r in data:
    print(f'{r["ticker"]} - {r["company_name"][:50]} - days_left: {r["days_left"]}')
