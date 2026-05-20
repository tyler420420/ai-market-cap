import re

with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the broken line and fix it - remove the leading whitespace that's wrong
# The line starts with "html +=" (no indent) but should be "    html +="
fixed = re.sub(r'\nhtml \+= \'\.pick-banner', r'\n    html += \'.pick-banner', content)

with open('ai_earnings_scanner.py', 'w', encoding='utf-8') as f:
    f.write(fixed)

print('Fixed!')
with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i in range(395, 402):
    print(f'{i+1}: {repr(lines[i][:70])}')