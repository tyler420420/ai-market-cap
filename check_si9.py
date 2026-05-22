import json

with open('ai_earnings_today.html','r', encoding='utf-8') as f:
    html = f.read()

idx = html.find('<script>var rowsData=')
script = html[idx:]
first_script_end = script.find('</script>')
json_text = script[17:first_script_end]

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

with open('si_data.txt','w', encoding='utf-8') as f:
    f.write(data_str)

print(f'Data len: {len(data_str)}, starts: {repr(data_str[:30])}')

# Try parsing
try:
    rows = json.loads(data_str)
    print(f'OK: {len(rows)} rows')
except Exception as e:
    print(f'Error: {e}')
    # Try stripping
    try:
        rows = json.loads(data_str.strip())
        print(f'OK after strip: {len(rows)} rows')
    except Exception as e2:
        print(f'Still error: {e2}')
        # Check bytes
        print(f'First 20 bytes: {data_str[:20].encode("utf-8").hex()}')