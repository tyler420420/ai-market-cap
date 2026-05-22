import re

with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Find the renderTable function and search within it for the IV cell
idx = c.find("function renderTable()")
if idx == -1:
    print('renderTable not found')
    exit()

snippet = c[idx:idx+5000]
# Look for IV cell and news cell
m = re.search(r"r\.iv[^;]*%</td>[^;]*newsHtml", snippet)
if m:
    print(f'Found: {repr(m.group())}')
else:
    print('Pattern not found, searching manually...')
    # Check for different quoting
    for pattern in [
        "r.iv+'%</td>'",
        "r.iv+'%</td>",
        'r.iv+"%</td>"',
        "r.iv+'%</td>'+newsHtml",
    ]:
        pos = snippet.find(pattern)
        if pos >= 0:
            print(f'Found "{pattern}" at {pos}')
            print(snippet[pos-5:pos+100])
            print('---')

# Also check if there's a pattern using the other quote style
m2 = re.search(r"html\+=.*r\.iv.*news", snippet)
if m2:
    print(f'Regex found: {repr(m2.group())}')