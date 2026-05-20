with open('ai_earnings_57day_20260519_2312.html', 'rb') as f:
    raw = f.read()

# Extract first script block (after <script>)
first_script_start = raw.find(b'<script>') + len(b'<script>')
first_script_end = raw.find(b'</script>')
script = raw[first_script_start:first_script_end]

# Save to file for manual inspection
with open('script_check.js', 'wb') as f:
    f.write(script)
print(f'Script length: {len(script)} bytes')

# Now let's find the issue by searching for problematic patterns
# Look for quote characters that could break JS

# Check the HTML in html+= strings - find unescaped quotes
import re

# Find all single-quoted strings that look like they have embedded quotes
# Pattern: '...' where ... contains another ' that isn't escaped
# Let's scan the script and check for issues

lines = script.decode('utf-8', errors='replace')
print(f'\nSearching for potential issues...')

# Look for "style=\"..." patterns that have embedded quotes
# Search for any line with 3+ double quotes close together
import re
# Find patterns like: "+r.company_name.substring(0,35) - what's between quotes here

# Let's just print the renderTable function and inspect it
rt_start = lines.find('function renderTable()')
rt_end = lines.find('document.addEventListener', rt_start)
rt = lines[rt_start:rt_end]
print('=== renderTable function ===')
print(rt)
print()

# Check for any > inside string concatenations that might look like HTML closing tags
# Specifically: find any </td> or similar in the HTML strings
print('Lines with </td>:')
for i, line in enumerate(rt.split(';')):
    if '</td>' in line:
        print(f'  Segment {i}: ...{line[-100:]}')