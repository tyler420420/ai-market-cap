c = open('ai_earnings_today.html', encoding='utf-8').read()
import re
sb_count = len(re.findall('Strong Buy', c))
print(f'Strong Buy occurrences: {sb_count} (should be 1)')
print(f'IPO Monzo present: {"SOONEST IPO" in c}')
print(f'IPO SpaceX present: {"SpaceX" in c}')
print(f'Body padding 0: {"padding:0" in c}')
print(f'No container 1400px: {"1400px" not in c}')