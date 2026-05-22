import json

with open('ai_earnings_today.html','r', encoding='utf-8') as f:
    html = f.read()

idx = html.find('<script>var rowsData=')
data_start = idx + len('<script>var rowsData=')
script_end = html.find('</script>', idx)
json_text = html[data_start:script_end]

depth = 0
in_str = False
esc = False
arr_end = 0
for i, ch in enumerate(json_text):
    if esc:
        esc = False
        continue
    if ch == '\\':
        esc = True
        continue
    if ch == '"':
        in_str = not in_str
        continue
    if in_str:
        continue
    if ch == '{':
        depth += 1
    elif ch == '}':
        depth -= 1
    elif ch == '[':
        depth += 1
    elif ch == ']':
        depth -= 1
        if depth == 0:
            arr_end = i + 1
            break

data_str = json_text[:arr_end]
rows = json.loads(data_str)
print(f'Parsed {len(rows)} stocks\n')
print('Stock | Short Int | Score | Days | Squeeze')
print('-' * 60)
for r in rows:
    si = r.get('short_int', 0) or 0
    score = r.get('score', 0)
    days = r.get('days_left', 0)
    sqz = r.get('squeeze', 0)
    sqz_str = 'SQUEEZE' if sqz else '----'
    si_str = str(si) + '%' if si > 0 else 'N/A'
    print(f'  {r["ticker"]:6} | {si_str:10} | {score:3} | {days:4}d | {sqz_str}')

has_sq = 'SQUEEZE' in html
print(f'\nSQUEEZE badge in HTML: {has_sq}')
print(f'Total SQUEEZE mentions: {html.count("SQUEEZE")}')