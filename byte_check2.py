with open('ai_earnings_57day_20260519_2312.html', 'rb') as f:
    raw = f.read()

# Extract first <script> block
script_start = raw.find(b'<script>') + len(b'<script>')
script_end = raw.find(b'</script>')
script = raw[script_start:script_end]

print('First 20 bytes of script:', script[:20].hex())
print('Starts with var rowsData:', script.startswith(b'var rowsData='))
print()

# Check isolated_test.html structure - why is line 48 inside the script?
with open('isolated_test.html', 'rb') as f:
    iso = f.read()

# Find the first script block
iso_script_start = iso.find(b'<script>') + len(b'<script>')
iso_script_end = iso.find(b'</script>')
iso_script = iso[iso_script_start:iso_script_end]

print('Isolated test first script bytes:', iso_script[:20].hex())
print('Isolated test first 200 chars:', iso_script[:200].decode('utf-8', errors='replace'))

# Count lines in the script
print('\nScript has', iso_script.count(b'\n'), 'LFs and', iso_script.count(b'\r\n'), 'CRLFs')

# Find what line 48 in isolated_test.html corresponds to
all_lines = iso.split(b'\n')
print('\nLine 46:', all_lines[45][:100])
print('Line 47:', all_lines[46][:100])
print('Line 48:', all_lines[47][:100])
print('Line 49:', all_lines[48][:100])
print('Line 50:', all_lines[49][:100])