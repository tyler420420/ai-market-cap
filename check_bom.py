with open('ai_earnings_57day_20260519_2237.html', 'rb') as f:
    raw = f.read()

# Check first 200 bytes for BOM or weird stuff
print('First 200 bytes (hex):')
print(raw[:200].hex())
print()
print('First 200 chars (repr):')
print(repr(raw[:200]))

# Check around script tag position (16843)
print('\n=== Around script tag position 16843 ===')
start = 16830
end = 16860
print(f'Bytes {start}-{end}: {raw[start:end].hex()}')
print(f'Chars: {raw[start:end].decode("utf-8", errors="replace")}')

# Check the VERY start of the first script block content
print('\n=== First 20 chars of script content ===')
script_start = raw.find(b'<script>')
if script_start != -1:
    content_start = script_start + len(b'<script>')
    print(f'Script content starts at byte {content_start}')
    print(f'Hex: {raw[content_start:content_start+40].hex()}')
    print(f'Chars: {repr(raw[content_start:content_start+40])}')

# Check for any null bytes or weird control chars in the script
script_content_start = raw.find(b'<script>') + len(b'<script>')
script_content_end = raw.find(b'</script>')
script_content = raw[script_content_start:script_content_end]

print(f'\nScript content length: {len(script_content)}')
print(f'Null bytes: {script_content.count(b"\x00")}')
print(f'Replacement char (ufffd): {script_content.count(b"\xef\xbf\xbd")}')

# Check for any non-ASCII in the script (shouldn't be any since it's JSON + ASCII JS)
non_ascii = [(i, b) for i, b in enumerate(script_content) if b > 127]
print(f'Non-ASCII bytes: {len(non_ascii)}')
if non_ascii[:5]:
    print(f'First 5: {non_ascii[:5]}')