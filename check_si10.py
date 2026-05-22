import json

with open('ai_earnings_today.html','r', encoding='utf-8') as f:
    html = f.read()

idx = html.find('<script>var rowsData=')
script = html[idx:]

# Better: find the exact start of the JSON array
data_start = idx + len('<script>var rowsData=')
print(f'Data starts at: {data_start}')
print(f'Char at that position: {repr(html[data_start:data_start+10])}')

first_script_end = script.find('</script>')
json_text = html[data_start:first_script_end]

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
print(f'Data len: {len(data_str)}, starts: {repr(data_str[:30])}')

rows = json.loads(data_str)
print(f'Parsed {len(rows)} stocks\n')
print(f'Stock | Short Int | Score | Days | Squeeze')
print('-' * 60)
for r in rows:
    si = r.get('short_int', 0) or 0
    score = r.get('score', 0)
    days = r.get('days_left', 0)
    sqz = '🔥' if si > 10 and days <= 10 else ''
    si_str = f"{si}%" if si > 0 else "N/A"
    print(f"  {r['ticker']:6} | {si_str:10} | {score:3} | {days:4}d | {sqz}")