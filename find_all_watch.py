c = open('ai_earnings_today.html', encoding='utf-8').read()
import re
matches = [m.start() for m in re.finditer('Watch</span></span>', c)]
print(f'Found {len(matches)} "Watch</span></span>" occurrences')
for i, idx in enumerate(matches):
    print(f'{i+1}. {repr(c[idx-200:idx+100])}')