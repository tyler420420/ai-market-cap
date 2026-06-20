import re

with open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html', 'r', encoding='utf-8') as f:
    h = f.read()

# Find all 3 Day column cells in static HTML
matches = re.findall(r'<td data-label="3 Day">[^<]*(?:<[^>]*>[^<]*</[^>]*>)*[^<]*</td>', h)
for m in matches[:3]:
    print(repr(m))
    print()
