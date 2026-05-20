with open('ai_earnings_57day_20260519_2237.html', 'r', encoding='utf-8') as f:
    c = f.read()

import re

# Find ALL <script> tags (not just content)
all_scripts = list(re.finditer(r'<script[^>]*>', c))
print(f'Total <script> tags: {len(all_scripts)}')
for i, m in enumerate(all_scripts):
    tag = m.group(0)
    print(f'Tag {i}: at {m.start()}: {repr(tag)}')
    # Show 20 chars after the tag
    after = c[m.end():m.end()+20]
    print(f'  After tag: {repr(after)}')

print()
# Find ALL </script> tags
all_closes = list(re.finditer(r'</script>', c))
print(f'Total </script> tags: {len(all_closes)}')
for i, m in enumerate(all_closes):
    print(f'Close {i}: at {m.start()}: {repr(c[max(0,m.start()-30):m.start()+20])}')

print()
# Show exact positions around each script boundary
print('=== Script block analysis ===')
for i, open_tag in enumerate(all_scripts):
    open_pos = open_tag.start()
    open_end = open_tag.end()
    if i < len(all_closes):
        close_pos = all_closes[i].start()
        close_end = all_closes[i].end()
        content = c[open_end:close_pos]
        print(f'\nScript {i}: opens at {open_pos}, closes at {close_pos}')
        print(f'  Content length: {len(content)}')
        print(f'  First 60: {repr(content[:60])}')
        print(f'  Last 60: {repr(content[-60:])}')
        # Count braces in content
        print(f'  Braces: {content.count("{")} open / {content.count("}")} close')
        # Check for ; inside content that might end early
        print(f'  Semicolons: {content.count(";")}')