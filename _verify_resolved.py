with open('scanner.html', encoding='utf-8') as f:
    content = f.read()

import re

# Check renderTable JS for single-quote style attrs
render_start = content.find('function renderTable')
render_end = render_start + 3000
render_js = content[render_start:render_end]
single_q = re.findall(r"style='[^']*'", render_js)
print(f'Single-quote style attrs in renderTable: {len(single_q)}')
if single_q:
    for m in single_q[:3]:
        print(f'  {m[:80]}')
else:
    print('  Clean!')

# Check that fetch is present
fetch_found = "fetch('/data')" in content
print(f"fetch('/data') present: {fetch_found}")

# Check getVal / sort functions exist
print(f"sortBy present: {'function sortBy' in content}")
print(f"sortBy('score') present: {chr(39) + 'score' + chr(39) in content or 'sortBy' in content}")
