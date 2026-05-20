with open('ai_earnings_57day_20260519_2312.html', 'rb') as f:
    raw = f.read()

first_script_start = raw.find(b'<script>') + len(b'<script>')
first_script_end = raw.find(b'</script>')
script = raw[first_script_start:first_script_end]

# Focus on position 1075 (the problematic area around the newsHtml function)
area = script[1060:1095]
print(f'Bytes 1060-1095: {area}')
print(f'As UTF-8: {area.decode("utf-8", errors="replace")}')
print(f'Hex: {area.hex()}')
print()

# Show ALL characters in the script that are > 127 (non-ASCII)
print('Non-ASCII bytes in entire script:')
non_ascii = [(i, b, hex(b)) for i, b in enumerate(script) if b > 127]
print(f'Count: {len(non_ascii)}')
for pos, byte, hx in non_ascii[:20]:
    print(f'  pos {pos}: byte {hx} = {chr(byte) if byte < 256 else "?"}')

# Check the emoji character (U+1F4F0 is 📰 but we use &#128240;)
# &#128240; should be & # 1 2 8 2 4 0 ; - all ASCII
print()
print('Checking for any non-ASCII in the html strings section (chars 1000-1250):')
for i, b in enumerate(script[1000:1250], start=1000):
    if b > 127:
        print(f'  pos {i}: {hex(b)} = {chr(b)}')