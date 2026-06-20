import re

with open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html', 'r', encoding='utf-8') as f:
    h = f.read()

# Fix static HTML rows: 3 Day column has bold spans - remove them
# Pattern: <td data-label="3 Day"><span style="font-weight:bold">$XXX</span><br>
# Replace with: <td data-label="3 Day">$XXX<br>
h2 = re.sub(
    r'<td data-label="3 Day"><span style="font-weight:bold">(\$[^<]+)</span><br>',
    r'<td data-label="3 Day">\1<br>',
    h
)
count = len(h) - len(h2)
print(f'Removed {count} chars of bold spans from static rows')

with open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html', 'w', encoding='utf-8') as f:
    f.write(h2)

print('Done')
