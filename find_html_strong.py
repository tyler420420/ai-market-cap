c = open('ai_earnings_scanner.py', encoding='utf-8').read()
# Find all html += that contain 'Strong Buy'
import re
matches = re.findall(r"html \+= '[^']*Strong Buy[^']*'", c)
print(f'Found {len(matches)} html += lines with Strong Buy:')
for m in matches:
    print(m[:150])
    print('---')