# Extract the first script block and save it for inspection
with open('ai_earnings_57day_20260519_2312.html', 'r', encoding='utf-8') as f:
    c = f.read()

s = c.find('<script>') + 8
e = c.find('</script>')
script = c[s:e]

# Write to file
with open('script_raw.txt', 'w', encoding='utf-8') as f:
    f.write(script)

# Count key things
print(f'Script length: {len(script)}')
print(f'Open braces: {script.count("{")}')
print(f'Close braces: {script.count("}")}')
print(f'Open parens: {script.count("(")}')
print(f'Close parens: {script.count(")")}')
print(f'Open brackets: {script.count("[")}')
print(f'Close brackets: {script.count("]")}')

# Check for any unescaped backticks (`) which might be in news titles
backtick_count = script.count('`')
print(f'\nBacktick count: {backtick_count}')

# Check for any unicode surrogate pairs or weird chars
import re
weird = [(i, ord(ch)) for i, ch in enumerate(script) if ord(ch) > 127 and ord(ch) not in range(0x80, 0xFF)]
print(f'Non-ASCII chars: {len(weird)}')
if weird[:10]:
    for pos, code in weird[:10]:
        print(f'  pos {pos}: U+{code:04X} = {repr(script[pos])}')

# Check around the specific error - print chars 330-350
print(f'\nChars 330-350: {repr(script[330:350])}')
# Print around position where error might be based on "Unexpected string"
# Let's find the renderTable call
rt_call = script.find('renderTable()')
print(f'renderTable() found at: {rt_call}')
print(f'Context: {repr(script[rt_call-20:rt_call+30])}')