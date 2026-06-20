import re, json

with open(r'C:\Users\Tyler_AI\Desktop\test_scanner_backup_20260617.html', encoding='utf-8') as f:
    backup = f.read()

# Find the JS block with rowsData
rows_data_pos = backup.find('var rowsData=')
script_start = backup.rfind('<script>', 0, rows_data_pos)
script_end = backup.find('</script>', rows_data_pos) + len('</script>')
js = backup[script_start:script_end]

# Find the renderTable function
render_start = js.find('function renderTable')
if render_start >= 0:
    render_end = js.find('sortBy(', render_start) + 50
    render_fn = js[render_start:render_end]
    print('renderTable function snippet:')
    print(repr(render_fn[:500]))
    print()

# Check the newsHtml function
news_start = js.find('function newsHtml')
if news_start >= 0:
    news_end = js.find(';}', news_start) + 2
    news_fn = js[news_start:news_end]
    print('newsHtml function:')
    print(repr(news_fn[:300]))
    print()

# Find the squeeze column pattern
squeeze_pos = js.find('squeeze')
if squeeze_pos >= 0:
    print('Squeeze pattern:')
    print(repr(js[max(0,squeeze_pos-50):squeeze_pos+100]))
    print()

# Now show what's in the tbody (static rows)
tbody_start = backup.find('<tbody')
tbody_end = backup.find('</tbody>')
tbody_content = backup[tbody_start:tbody_end+8]
print(f'Tbody content: {len(tbody_content)} chars')
print('First 200:')
print(repr(tbody_content[:200]))
print()
print('Last 200:')
print(repr(tbody_content[-200:]))
