with open('ai_earnings_57day_20260519_2237.html', 'r', encoding='utf-8') as f:
    c = f.read()

import re

# Check for </script> anywhere in the HTML (even inside strings)
positions = []
for m in re.finditer(r'</script>', c):
    positions.append(m.start())

print(f'</script> occurrences: {len(positions)}')
for pos in positions:
    ctx = c[max(0, pos-50):pos+30]
    print(f'\nAt pos {pos}:')
    print(repr(ctx))

# Also check for unescaped </ within the first script block
blocks = list(re.finditer(r'<script[^>]*>(.*?)</script>', c, re.DOTALL))
block0 = blocks[0]
content = block0.group(1)
idx = content.find('</script')
if idx >= 0:
    print(f'\n!!! Found </script> INSIDE first script block at offset {idx}')
    print(repr(content[idx-50:idx+50]))