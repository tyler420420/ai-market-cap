with open('ai_earnings_57day_20260519_2237.html', 'r', encoding='utf-8') as f:
    c = f.read()

import re

# Find the exact transition from rowsData JSON to sortCol
start = c.find('var rowsData=')
end = c.find('var sortCol')
before = c[start:end]
after = c[end:end+200]

print('=== Around rowsData -> sortCol ===')
print(f'rowsData content length: {len(before)}')
print(f'First 200: {repr(before[:200])}')
print()
print(f'sortCol context:')
print(repr(after))

# Check for any stray characters between rowsData and sortCol
mid = before[-10:]
print(f'\nLast 10 chars of rowsData section: {repr(mid)}')
print(f'Char codes: {[ord(ch) for ch in mid]}')