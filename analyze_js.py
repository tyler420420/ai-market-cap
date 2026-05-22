with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Find the script block starting with rowsData
idx = c.find("html += '<script>var rowsData=")
print('rowsData script at:', idx)

# Find the next html += line after
idx2 = c.find("\n    html += ", idx + 10)
print('Next html += at:', idx2)

# The whole JS block is from idx to idx2 (line 529)
script_block = c[idx:idx2]
with open('script_block.txt', 'w', encoding='utf-8') as f:
    f.write(script_block)
print('Written, length:', len(script_block))