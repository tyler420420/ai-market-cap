with open('ai_earnings_57day_20260519_2237.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Find the <table> opening tag
table_pos = c.find('<table')
print(f'<table> position: {table_pos}')
print(f'Surrounding: {repr(c[table_pos:table_pos+50])}')

# Find the table headers / thead
thead_pos = c.find('<thead')
print(f'\n<thead> position: {thead_pos}')
# Show thead content
print(f'Thead around: {repr(c[thead_pos:thead_pos+200])}')

# Find the closing thead
thead_close = c.find('</thead>')
print(f'\n</thead> position: {thead_close}')
print(f'After </thead>: {repr(c[thead_close:thead_close+30])}')

# Find tbody
tbody_pos = c.find('<tbody')
print(f'\n<tbody> position: {tbody_pos}')
print(f'Tbody surrounding: {repr(c[tbody_pos:tbody_pos+50])}')

# Find </table>
table_close = c.find('</table>')
print(f'\n</table> position: {table_close}')
print(f'Before </table>: {repr(c[table_close-50:table_close])}')

# Show the actual table section
print('\n=== FULL TABLE SECTION ===')
print(c[table_pos:table_close+8])