import json, re, sys

with open('ai_earnings_today.html','r', encoding='utf-8') as f:
    html = f.read()

# Extract rowsData JSON
idx = html.find('var rowsData=')
if idx == -1:
    print('rowsData not found in HTML')
    sys.exit(1)

# Find the JSON object start and end
json_start = idx + 12  # len('var rowsData=')
depth = 0
json_end = json_start
in_str = False
esc = False
for i in range(json_start, len(html)):
    ch = html[i]
    if esc:
        esc = False
        continue
    if ch == '\\':
        esc = True
        continue
    if ch == '"' and not esc:
        in_str = not in_str
        continue
    if in_str:
        continue
    if ch == '{':
        depth += 1
    elif ch == '}':
        depth -= 1
        if depth == 0:
            json_end = i + 1
            break

json_str = html[json_start:json_end]
rows = json.loads(json_str)

print(f'Stock | Short Int % | Score | Days | Squeeze Signal')
print('-' * 65)
for r in rows:
    si = r.get('short_int', 0)
    score = r.get('score', 0)
    days = r.get('days_left', 0)
    # Squeeze threshold: SI > 10% AND days <= 10
    sqz = '🔥 SQZ' if si and si > 10 and days <= 10 else ''
    si_str = f"{si}%" if si else "N/A"
    print(f"{r.get('ticker','?'):6} | {si_str:12} | {score:5} | {days:4}d | {sqz}")