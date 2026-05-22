import json

with open('ai_earnings_today.html','r', encoding='utf-8') as f:
    html = f.read()

idx = html.find('<script>var rowsData=')
script = html[idx:]
first_script_end = script.find('</script>')
json_text = script[17:first_script_end]  # skip '<script>var rowsData=' (17 chars)

# The script contains BOTH the rowsData array AND the JS code after it
# The array ends when we close the outer ] followed by ;
# We need to find the first ] that's the end of the array, not inside JS code

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
print(f'Data string length: {len(data_str)}')
print(f'Last 100 chars: {data_str[-100:]}')

rows = json.loads(data_str)
print(f'\nParsed {len(rows)} stocks\n')
print(f'Stock | Short Int | Score | Days | Squeeze')
print('-' * 60)
for r in rows:
    si = r.get('short_int', 0) or 0
    score = r.get('score', 0)
    days = r.get('days_left', 0)
    sqz = '🔥' if si > 10 and days <= 10 else ''
    si_str = f"{si}%" if si > 0 else "N/A"
    print(f"  {r['ticker']:6} | {si_str:10} | {score:3} | {days:4}d | {sqz}")