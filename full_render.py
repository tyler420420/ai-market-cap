with open('ai_earnings_57day_20260519_2237.html', 'r', encoding='utf-8') as f:
    c = f.read()

import re
# Find the FULL renderTable function - not truncated
start = c.find('function renderTable()')
end = c.find('</script>', start)
render_section = c[start:end]

print('Full renderTable section:')
print(render_section)
print()
print('Length:', len(render_section))