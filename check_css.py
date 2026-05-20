with open('ai_earnings_57day_20260519_2312.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Find style block
style_start = c.find('<style>')
style_end = c.find('</style>')
style = c[style_start:style_end]

# Check for tbody display rules
import re
rules_with_tbody = [r for r in style.split('}') if 'tbody' in r.lower() or 'table' in r.lower()]
for r in rules_with_tbody:
    print(repr(r[:200]))

print()
# Look for max-height, height, overflow rules on table
table_rules = re.findall(r'#stockTable[^}]*\}', style)
for t in table_rules:
    print('Table rule:', repr(t))