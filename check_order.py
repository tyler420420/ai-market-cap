with open('ai_earnings_57day_20260519_2237.html', 'r', encoding='utf-8') as f:
    c = f.read()

import re

# Find the first script block content
start_script = c.find('<script>')
end_script = c.find('</script>')
content = c[start_script+8:end_script]

# Extract var declarations in order
import re
lines = content.split('\n')
vars_found = []
for line in lines:
    line = line.strip()
    if line.startswith('var ') and '(' not in line:
        name = line.split('=')[0].replace('var ', '').strip()
        vars_found.append(name)

print('Variables defined in order:')
for i, v in enumerate(vars_found):
    print(f'  {i}: {v}')

print()

# Check for DOMContentLoaded registration
dcl_lines = [l for l in lines if 'DOMContentLoaded' in l or 'renderTable' in l]
print('Lines mentioning renderTable or DOMContentLoaded:')
for l in dcl_lines:
    print(f'  {repr(l.strip())}')

# Now check: is renderTable defined BEFORE or AFTER the addEventListener line?
render_def_line = None
dcl_line = None
for i, line in enumerate(lines):
    if 'function renderTable' in line:
        render_def_line = i
    if 'DOMContentLoaded' in line:
        dcl_line = i

print(f'\nrenderTable defined at line: {render_def_line}')
print(f'DOMContentLoaded registered at line: {dcl_line}')

# Check if renderTable() is called anywhere before the addEventListener
pre_dcl = lines[:dcl_line] if dcl_line else lines
early_calls = [i for i, l in enumerate(pre_dcl) if 'renderTable()' in l and 'function' not in l]
print(f'renderTable() called before addEventListener: {early_calls}')