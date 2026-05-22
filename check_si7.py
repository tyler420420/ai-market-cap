import json

with open('ai_earnings_today.html','r', encoding='utf-8') as f:
    html = f.read()

idx = html.find('<script>var rowsData=')
script = html[idx:]
first_script_end = script.find('</script>')
json_start = script.find('=') + 1
json_text = script[json_start:first_script_end]

with open('debug_json.txt','w', encoding='utf-8') as f:
    f.write(json_text)

# Write bytes to check for encoding issues
with open('debug_json_bytes.txt','wb') as f:
    f.write(json_text.encode('utf-8'))

print(f'JSON length: {len(json_text)}')
print(f'First 200 chars: {json_text[:200]}')
print(f'Last 200 chars: {json_text[-200:]}')

# Check for problematic chars
for i, ch in enumerate(json_text[:500]):
    if ord(ch) > 127:
        print(f'Non-ASCII at {i}: {repr(ch)}')