with open('ai_earnings_57day_20260519_2237.html', 'r', encoding='utf-8') as f:
    c = f.read()

import re

# Find ALL script blocks
blocks = list(re.finditer(r'<script[^>]*>(.*?)</script>', c, re.DOTALL))
print(f'Total script blocks: {len(blocks)}')
for i, b in enumerate(blocks):
    content = b.group(1).strip()
    first_50 = content[:50] if content else '(empty)'
    print(f'\nBlock {i}: pos {b.start()}-{b.end()}, len={len(content)}')
    print(f'  First 50: {repr(first_50)}')
    # Check for obvious JS syntax issues
    if 'function' in content or 'var ' in content:
        print(f'  Has functions/vars: YES')
        if content.count('{') != content.count('}'):
            print(f'  BRACE MISMATCH: {content.count("{")} opens vs {content.count("}")} closes')
    else:
        print(f'  Inline JS: NO (HTML content inside script?)')