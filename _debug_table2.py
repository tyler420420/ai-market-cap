with open(r'C:\Users\Tyler_AI\Desktop\test_scanner.html', encoding='utf-8') as f:
    content = f.read()

# Find tbody area
idx = content.find('<tbody id="stockTableBody"')
print(f'tbody at: {idx}')
print(f'After tbody: {repr(content[idx:idx+80])}')

# Find renderTable function
idx2 = content.find('function renderTable')
print(f'renderTable at: {idx2}')
if idx2 >= 0:
    print(f'First 200: {repr(content[idx2:idx2+200])}')

# Find sortBy call
idx3 = content.find("sortBy('score')")
print(f'sortBy at: {idx3}')
if idx3 >= 0:
    print(f'Context: {repr(content[idx3-50:idx3+20])}')

# Find DOMContentLoaded
idx4 = content.find('DOMContentLoaded')
print(f'DOMContentLoaded at: {idx4}')
if idx4 >= 0:
    print(f'Context: {repr(content[idx4-30:idx4+60])}')

# Check what's between the <script> at 29548 and tbody
start = 29548 + len('<script>')
print(f'\nBetween script start and tbody (first 500 chars):')
print(repr(content[start:start+500]))
