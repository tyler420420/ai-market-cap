import requests, secrets, time

token = secrets.token_hex(32)
expires = int(time.time()) + 86400
s = requests.Session()
s.cookies.set('scanner_session', f'{token}|{expires}')
r = s.get('https://aismarketcap.com/scanner', timeout=15)

# Show what's at the error position (6876)
pos = 6876
print('Around position 6876:')
print(repr(r.text[pos-100:pos+100]))
print()

# Also check if there are double-encoded ampersands
print('Double-amp occurrences:', r.text.count('&amp;&amp;'))

# Find all &amp; in JS context (inside script tags)
import re
for b in re.finditer(r'<script[^>]*>(.*?)</script>', r.text, re.DOTALL):
    content = b.group(1)
    if '&amp;&amp;' in content or '&amp;' in content:
        idx = content.find('&amp;')
        print(f'Script block at {b.start()}, &amp; at offset {idx}:')
        print(repr(content[max(0,idx-50):idx+50]))