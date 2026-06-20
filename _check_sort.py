html = open('ai_earnings_today.html').read()

# Check ALL th headers - are they all clickable?
import re
headers = re.findall(r'<th[^>]*onclick[^>]*>', html)
print('Clickable headers:')
for h in headers:
    col = re.search(r"sortBy\('([^']+)'\)", h)
    if col:
        print(f'  {col.group(1)}')

print()
# Check if Days th has cursor style
m = re.search(r'<th[^>]*data-col="days_left"[^>]*>', html)
print('Days th full tag:', m.group() if m else 'NOT FOUND')
print()
print('Does th have cursor:pointer?', 'cursor' in (m.group() if m else ''))
