import json, re
with open('ai_earnings_today.html','r') as f:
    html = f.read()
m = re.search(r'const rowsData = (\[.*?\]);', html, re.DOTALL)
if not m:
    print('rowsData not found')
    exit()
rows = json.loads(m.group(1))
with open('si_output.txt','w') as out:
    out.write(f'Stock, Short Int %, Score, Days\n')
    for r in rows:
        out.write(f"{r.get('ticker','?')}: SI={r.get('short_int','?')} Score={r.get('score','?')} Days={r.get('days_left','?')}\n")
print(f'Checked {len(rows)} stocks')