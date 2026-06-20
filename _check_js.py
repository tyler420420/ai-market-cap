import json, re

with open('scanner.html', encoding='utf-8') as f:
    html = f.read()

# Find the JS block after </table>
table_close = html.find('</table>')
js_start = html.find('<script>', table_close)
js_end = html.find('</script>', js_start) + len('</script>')
js = html[js_start:js_end]

print(f'JS block: {len(js)} chars')
print(f'Contains sortBy call: {"sortBy" in js}')
print(f'Contains renderTable call: {"renderTable" in js}')
print(f'First 200: {repr(js[:200])}')

# Find sortBy call position
sortby_pos = js.find('sortBy')
print(f'sortBy at: {sortby_pos}')
if sortby_pos >= 0:
    print(f'Context: {repr(js[sortby_pos-20:sortby_pos+30])}')

# Remove the sortBy call that would trigger broken renderTable
# Keep everything else: rowsData, getVal, updateArrows, fmtMktcap, scoreColor, newsHtml, renderTable (unused)
# Actually, let's keep sortBy but remove the renderTable call from it
# Better: remove the sortBy call entirely, just load data

# Option: remove sortBy('days_left') or sortBy('score') call
# Find the last sortBy call in the JS
last_sortby = js.rfind('sortBy(')
print(f'Last sortBy: {repr(js[last_sortby:last_sortby+20])}')
