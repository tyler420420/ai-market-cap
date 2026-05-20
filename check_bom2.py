with open('ai_earnings_57day_20260519_2312.html', 'rb') as f:
    raw = f.read()

pos = raw.find(b'<script>')
print('Byte positions:')
print(f'<script> at: {pos}')
print(f'First script content starts at: {pos + 8}')
print(f'First 60 bytes of script content:')
chunk = raw[pos+8:pos+8+60]
print(f'  Hex: {chunk.hex()}')
print(f'  Chars: {chunk.decode("utf-8", errors="replace")}')

# The error is at line 48 - let's count newlines in the raw HTML up to position
# Actually, let me check: is the file using LF or CRLF?
print(f'\nFile uses CRLF: {b"\r\n" in raw}')
print(f'File uses LF: {b"\n" in raw}')

# Show the exact area around the 48th line in the HTML file
# But first, count lines in the script block
script_start = pos + 8
script_end = raw.find(b'</script>')
script = raw[script_start:script_end]
print(f'\nScript content ({len(script)} bytes):')
print(f'  LF count: {script.count(b"\n")}')
print(f'  CRLF count: {script.count(b"\r\n")}')

# Find the raw bytes of the script - specifically look for any \r\n at the beginning
print(f'\nFirst 30 bytes: {script[:30].hex()} = {script[:30]}')