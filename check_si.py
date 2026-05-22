import json, re
with open('ai_earnings_today.html','r') as f:
    html = f.read()
m = re.search(r'const rowsData = (\[.*?\]);', html, re.DOTALL)
if m:
    rows = json.loads(m.group(1))
    print(f'Stock, Short Int %, Score, Days')
    for r in rows[:10]:
        print(f"{r['ticker']}: SI={r.get('short_int','?')}% Score={r.get('score','?')} Days={r.get('days_left','?')}")