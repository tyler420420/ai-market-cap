with open('ai_earnings_57day_20260519_2256.html', 'rb') as f:
    raw = f.read()

# Find script start, extract JSON array
script_start = raw.find(b'<script>') + len(b'<script>')
script_end = raw.find(b'</script>')
content = raw[script_start:script_end]

# Find the [ ] bounds of the JSON array
first_bracket = content.find(b'[')
last_bracket = content.rfind(b']')
json_part = content[first_bracket:last_bracket+1]

print(f'Total script content: {len(content)} bytes')
print(f'JSON starts at offset: {first_bracket}')
print(f'JSON ends at offset: {last_bracket}')
print(f'JSON length: {len(json_part)}')
print(f'First 20 chars: {repr(json_part[:20])}')
print(f'Last 20 chars: {repr(json_part[-20:])}')

# Try parse
try:
    import json
    data = json.loads(json_part)
    print(f'Parsed OK: {len(data)} rows')
except Exception as ex:
    print(f'PARSE ERROR: {ex}')
    # Find position in the JSON
    err_msg = str(ex)
    import re
    m = re.search(r'position (\d+)', err_msg)
    if m:
        pos = int(m.group(1))
        print(f'Error at JSON char {pos}')
        # Show context
        start = max(0, pos-50)
        end = min(len(json_part), pos+50)
        print(f'Around error: {repr(json_part[start:end])}')
        # Find what JSON looks like at the error
        print(f'Char at error: {repr(json_part[pos:pos+20])}')

# Check for any ] characters within company names or news
print('\n=== All ] positions in script content ===')
for i, b in enumerate(content):
    if b == ord(']'):
        ctx = content[max(0,i-30):i+30]
        print(f'  pos {i}: {repr(ctx)}')