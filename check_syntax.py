with open('ai_earnings_57day_20260519_2237.html', 'r', encoding='utf-8') as f:
    c = f.read()

import re

blocks = list(re.finditer(r'<script[^>]*>(.*?)</script>', c, re.DOTALL))
print(f'Total script blocks: {len(blocks)}')

for i, b in enumerate(blocks):
    content = b.group(1).strip()
    opens = content.count('{')
    closes = content.count('}')
    parens_open = content.count('(')
    parens_close = content.count(')')
    brackets_open = content.count('[')
    brackets_close = content.count(']')

    print(f'\nBlock {i}: len={len(content)}')
    print(f'  Braces: {opens} open, {closes} close - {"OK" if opens == closes else "MISMATCH!"}')
    print(f'  Parens: {parens_open} open, {parens_close} close - {"OK" if parens_open == parens_close else "MISMATCH!"}')
    print(f'  Brackets: {brackets_open} open, {brackets_close} close - {"OK" if brackets_open == brackets_close else "MISMATCH!"}')

    if opens != closes:
        print(f'  BRACE MISMATCH - searching for issue...')
        # Try to find where
        depth = 0
        for j, ch in enumerate(content):
            if ch == '{': depth += 1
            elif ch == '}':
                depth -= 1
                if depth < 0:
                    print(f'    Extra }} at position {j}: {repr(content[max(0,j-30):j+30])}')
                    break