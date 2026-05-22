import json, re, sys

with open('ai_earnings_today.html','r', encoding='utf-8') as f:
    html = f.read()

# Find start of rowsData JSON array
idx = html.find('var rowsData=')
if idx == -1:
    print('rowsData not found')
    sys.exit(1)

print(f'Found at index: {idx}')
print(f'Context (200 chars):')
print(html[idx:idx+200])
print()

# Try to extract using regex
m = re.search(r'var rowsData=(\[\{.*\}\])', html, re.DOTALL)
if m:
    print('Regex matched, len:', len(m.group(1)))
else:
    print('Regex did not match - trying manual extraction')

# Manual: find [
arr_start = html.find('[', idx + 12)
print(f'Array starts at: {arr_start}')

# Find matching ]
depth = 0
in_str = False
esc = False
for i in range(arr_start, min(arr_start + 100000, len(html))):
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
            arr_end = i + 1
            json_str = html[arr_start:arr_end]
            with open('json_debug.txt','w') as f:
                f.write(json_str[:5000])
            print(f'JSON extracted, len={len(json_str)}, first 500 chars written')
            break