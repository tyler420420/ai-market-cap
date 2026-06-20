with open('scanner.html', encoding='utf-8') as f:
    html = f.read()

# Find ALL script blocks
import re
scripts = [(m.start(), m.end()) for m in re.finditer('<script>', html)]
print(f'Script blocks: {len(scripts)}')
for i, (s, e) in enumerate(scripts):
    end = html.find('</script>', s)
    tag = html[s:end+9]
    print(f'  Block {i+1}: {repr(tag[:100])}')

# The rowsData script is the one with 'var rowsData='
rows_data_pos = html.find('var rowsData=')
print(f'\nrowsData at: {rows_data_pos}')
script_for_rows = html.rfind('<script>', 0, rows_data_pos)
print(f'Script block for rowsData: starts at {script_for_rows}')
end_tag = html.find('</script>', script_for_rows)
print(f'Script ends at: {end_tag}')
print(f'Last 100 chars of script: {repr(html[end_tag-100:end_tag+9])}')

# Remove sortBy('days_left'); from THIS script block only
script_content = html[script_for_rows:end_tag+9]
if "sortBy('days_left');" in script_content:
    new_script = script_content.replace("sortBy('days_left');", "")
    html = html[:script_for_rows] + new_script + html[end_tag+9:]
    print('Removed sortBy call')
else:
    print('sortBy call not found - may already be removed')

# Save
with open('scanner.html', 'w', encoding='utf-8') as f:
    f.write(html)
import shutil
shutil.copy('scanner.html', r'C:\Users\Tyler_AI\Desktop\test_scanner.html')
print(f'scanner.html: {len(html)} bytes')
