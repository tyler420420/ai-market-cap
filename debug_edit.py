path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find all occurrences of the ticker pattern (original)
import re
# Count html+ patterns with <td> that don't have data-label
all_td = re.findall(r"html\+='<td[^>]*>", content)
print(f'Total html+ td: {len(all_td)}')
without = [t for t in all_td if 'data-label' not in t]
print(f'Without data-label: {len(without)}')
for t in without[:5]:
    print(f'  {t[:60]}')

# Check if there's a problem in the sortCol line
idx = content.find("var sortCol")
if idx >= 0:
    seg = content[idx:idx+500]
    # Check for mismatched quotes
    # Look for patterns that might break the string
    print(f'\nsortCol section snippet:')
    print(repr(seg[:200]))