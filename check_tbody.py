with open(r'C:\Users\Tyler_AI\Desktop\test_scanner.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Find tbody content
idx = c.find('stockTableBody')
idx2 = c.find('</tbody>', idx)
print('tbody length:', idx2 - idx)
print('First 500 chars of tbody:')
print(repr(c[idx:idx+500]))
print()
# Check if it has actual row data
if '<td>' in c[idx:idx2]:
    count = c[idx:idx2].count('<tr')
    print(f'Number of <tr in tbody: {count}')
else:
    print('tbody is EMPTY - JS renders all rows')