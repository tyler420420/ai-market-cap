with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Check for problematic patterns in the new JS
script_start = code.find("html += '<script>'")
script_end = code.find("</script>'", script_start) + 10
script_block = code[script_start:script_end]

amp_count = script_block.count('&amp;')
print('&amp; in script:', amp_count)
print('&& in script:', script_block.count('&&'))
print('Length:', len(script_block))
print()
print('--- Script preview (first 500) ---')
print(script_block[:500])
print()
print('--- Script preview (last 300) ---')
print(script_block[-300:])