with open(r'C:\Users\Tyler_AI\.mavis\sessions\mvs_41a119d03ae849d59a2cdecd57e77d10\workspace\ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Check what the actual th CSS looks like
import re
# Find th CSS line
th_match = re.search(r'th\{[^}]+\}', c)
if th_match:
    print('Current th CSS:')
    print(repr(th_match.group(0)[:300]))

# Check headers tuple
idx = c.find("headers = [")
if idx >= 0:
    print('\nHeaders section:')
    print(repr(c[idx:idx+500]))

# Check green divider
idx2 = c.find('border-right')
if idx2 >= 0:
    print('\nDivider CSS:')
    print(repr(c[idx2-20:idx2+100]))