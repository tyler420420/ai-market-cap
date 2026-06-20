with open(r'C:\Users\Tyler_AI\Desktop\test_scanner.html', encoding='utf-8') as f:
    content = f.read()

# Find stockTableBody
idx = content.find('stockTableBody')
print(f'stockTableBody found at: {idx}')
print(f'Context: {repr(content[max(0,idx-100):idx+100])}')

# Check for <tbody
idx3 = content.find('<tbody')
print(f'<tbody found: {idx3}')
if idx3 >= 0:
    print(f'Context: {repr(content[idx3:idx3+80])}')

# Check for <tr in the body
idx4 = content.find('<tr')
print(f'<tr found at: {idx4}')
if idx4 >= 0:
    print(f'Context: {repr(content[idx4:idx4+80])}')

# Check end of file
print(f'Last 200 chars: {repr(content[-200:])}')
