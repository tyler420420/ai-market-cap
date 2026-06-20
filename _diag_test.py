import re
from pathlib import Path

test = Path(r'C:\Users\Tyler_AI\Desktop\test_scanner.html')
html = test.read_text(encoding='utf-8')

# How many times does 'var rowsData=' appear?
count = html.count('var rowsData=')
print('var rowsData= appears:', count, 'times')

# Find all occurrences
idx = 0
occurrences = []
while True:
    idx = html.find('var rowsData=', idx)
    if idx < 0:
        break
    occurrences.append(idx)
    idx += 1
print('Occurrences at:', occurrences)

# Check if it fetches from /data
fetch_data = '/data' in html and 'fetch' in html
print('Fetches from /data?:', fetch_data)

# Check the first few bytes of rowsData
if occurrences:
    first = occurrences[0]
    print('First rowsData starts with:', repr(html[first:first+30]))
    # Find the closing ]
    arr_depth = 0
    end = first
    for i in range(first + 13, len(html)):
        if html[i] == '[': arr_depth += 1
        elif html[i] == ']':
            arr_depth -= 1
            if arr_depth == 0:
                end = i
                break
    print('First rowsData ends at:', end)
    print('First rowsData length:', end - first - 13 + 1)
    snippet = html[first + 13:first + 100]
    print('First 80 chars of data:', repr(snippet))

    # Check if last ticker is different from first
    import json
    try:
        data = json.loads(html[first + 13:end + 1])
        print('JSON parse OK,', len(data), 'stocks')
        print('First ticker:', data[0]['ticker'], '$' + str(data[0]['price']), data[0]['days_left'], 'd')
        print('Last ticker:', data[-1]['ticker'], '$' + str(data[-1]['price']), data[-1]['days_left'], 'd')
    except Exception as e:
        print('JSON parse error:', e)
