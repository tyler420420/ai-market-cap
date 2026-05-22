c = open('ai_earnings_today.html', encoding='utf-8').read()

# Find the old duplicate counter section - appears after IPO boxes and before How It Works
# It looks like: <span...>7</span> <span...>Strong Buy</span></span>...Watch</span></div><div...><a href="/about"

# Find ALL occurrences of "Strong Buy" to identify duplicates
import re
matches = [m.start() for m in re.finditer('Strong Buy', c)]
print(f'Found {len(matches)} "Strong Buy" occurrences')
for i, idx in enumerate(matches):
    print(f'{i+1}. {c[idx-50:idx+30]}')

# The second occurrence is the old duplicate we want to remove
if len(matches) >= 2:
    # Find the section between first and second "Strong Buy" that contains the duplicate
    first = matches[0]
    second = matches[1]
    # Find the "Watch</span></span>" pattern that precedes the second Strong Buy
    dup_start = c.find('Watch</span></span>', first)
    dup_end = c.find('How It Works', second) - len('How It Works')
    print(f'\nDuplicate section: {repr(c[dup_start-20:dup_end+200])}')