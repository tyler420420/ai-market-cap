with open('ai_earnings_57day_20260520_0037.html', 'rb') as f:
    raw = f.read()
print('sorted-asc:', b'sorted-asc' in raw)
print('sorted-desc:', b'sorted-desc' in raw)
print('updateArrows():', b'updateArrows()' in raw)
print('data-col ticker:', b'data-col="ticker"' in raw)
print('th onclick sortBy:', b'onclick="sortBy' in raw)
print('function updateArrows:', b'function updateArrows' in raw)
print('cursor:pointer in CSS:', b'cursor:pointer' in raw)
print()
# Show the CSS around sorted-asc
idx = raw.find(b'sorted-asc')
if idx >= 0:
    print('Context around sorted-asc:')
    print(raw[idx-30:idx+80])