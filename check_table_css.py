with open('ai_earnings_57day_20260519_2237.html', 'r', encoding='utf-8') as f:
    c = f.read()

import re

# Extract ALL CSS rules related to table/tbody/tr/td
style_match = re.search(r'<style>(.*?)</style>', c, re.DOTALL)
css = style_match.group(1)

print('=== TABLE-RELATED CSS ===')
for rule in css.split('}'):
    r = rule.strip()
    if any(x in r for x in ['table', 'tbody', 'tr', 'td', 'th']):
        print(r + '}')
        print()