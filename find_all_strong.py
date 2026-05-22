c = open('ai_earnings_today.html', encoding='utf-8').read()
import re
matches = [m.start() for m in re.finditer('Strong Buy', c)]
print(f'Strong Buy occurrences: {len(matches)}')
for i, idx in enumerate(matches):
    print(f'\n{i+1}. BEFORE: {repr(c[idx-200:idx])}')
    print(f'{i+1}. AFTER: {repr(c[idx:idx+100])}')