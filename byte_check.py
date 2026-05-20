with open('ai_earnings_57day_20260519_2312.html', 'rb') as f:
    raw = f.read()

# Extract first <script> block
script_start = raw.find(b'<script>') + len(b'<script>')
script_end = raw.find(b'</script>')
script = raw[script_start:script_end]

# Save it
with open('script_bytes.bin', 'wb') as f:
    f.write(script)

# Now let's check: is there anything BEFORE 'var rowsData=' in the first 20 bytes?
first20 = script[:20]
print(f'First 20 bytes of script: {first20.hex()}')
print(f'First 20 chars: {first20}')
print(f'Starts with var rowsData: {script.startswith(b"var rowsData=")}')

# Find 'var rowsData=' position
vrd_pos = script.find(b'var rowsData=')
print(f'\n"var rowsData=" found at position: {vrd_pos}')

# Check what bytes are at vrd_pos - vrd_pos
print(f'Bytes before "var rowsData=": {script[:vrd_pos].hex()}')
print(f'Chars before: {script[:vrd_pos]}')

# The error says 'rowsData is not defined' AT LINE 48
# But we know the script content has no newlines and starts with 'var rowsData='
# This means line 48 of the HTML file = line (48 - lines before script) of the script content
# Lines before first script in HTML = lines up to <script> opening tag
lines_before_script = raw[:raw.find(b'<script>')].count(b'\n')
print(f'\nLines before <script> in HTML: {lines_before_script}')
print(f'So line 48 in HTML = line {48 - lines_before_script} in script content')
print(f'Script content has {script.count(b\"\n\")} newlines, {script.count(b\"\r\n\")} CRLF')

# The script has ZERO newlines. So line 48 of the HTML cannot be inside the script content
# unless... the HTML file uses different line endings than expected

# Check the isolated_test.html to see how it structured things
# Actually let me check: in the HTML, is the <script> tag on its own line or same as content?
# Let's see the exact structure around the script tag
script_tag_pos = raw.find(b'<script>')
print(f'\nAround <script> at pos {script_tag_pos}:')
print(raw[script_tag_pos-50:script_tag_pos+60])

# And around </script>
close_tag_pos = raw.find(b'</script>')
print(f'\nAround </script> at pos {close_tag_pos}:')
print(raw[close_tag_pos-30:close_tag_pos+15])