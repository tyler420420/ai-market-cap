import json, re

with open('scanner.html', encoding='utf-8') as f:
    html = f.read()

# Find the JS block after </table>
table_close = html.find('</table>')
js_start = html.find('<script>', table_close)
js_end = html.find('</script>', js_start) + len('</script>')
js = html[js_start:js_end]

# Remove the sortBy('days_left') call at the end - it's what triggers the broken renderTable
# The static HTML rows display fine without JS
clean_js = js.rstrip()
if clean_js.endswith('sortBy(\'days_left\');'):
    clean_js = clean_js[:-len("sortBy('days_left');")].rstrip()
elif clean_js.endswith('sortBy("days_left");'):
    clean_js = clean_js[:-len('sortBy("days_left");')].rstrip()

# Also try to find and remove any trailing sortBy call
trailing_sort = re.search(r'sortBy\([^)]+\);\s*$', clean_js)
if trailing_sort:
    clean_js = clean_js[:trailing_sort.start()].rstrip() + ';'
    print(f'Removed trailing sortBy: {trailing_sort.group()}')
else:
    print('No trailing sortBy found')

new_html = html[:js_start] + clean_js + '</script>' + html[js_end:]

# Verify
single_q = re.findall(r"style='[^']*'", new_html[table_close:table_close+200])
print(f'Single-quote style attrs near table close: {len(single_q)}')

# Count double-quoted attrs in JS (should be fine)
double_q = re.findall(r'style="[^"]*"', new_html[table_close:table_close+500])
print(f'Double-quote style attrs near table close: {len(double_q)}')

# Save
with open('scanner.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

print(f'\nFinal scanner.html: {len(new_html)} bytes')
print(f'JS ends with: {repr(clean_js[-50:])}')
