import requests, secrets, time, re

token = secrets.token_hex(32)
expires = int(time.time()) + 86400
s = requests.Session()
s.cookies.set('scanner_session', f'{token}|{expires}')
r = s.get('https://aismarketcap.com/scanner', timeout=15)
print('Status:', r.status_code)
print('Size:', len(r.text))

# Find chat button
m = re.search(r'id="chat-btn"[^>]*>', r.text)
if m:
    print('\nChat button:', r.text[m.start():m.start()+150])

# Find toggleChat function
m2 = re.search(r'function toggleChat', r.text)
print('toggleChat function found:', bool(m2))
if m2:
    print('At position:', m2.start())
    print('Context:', r.text[m2.start():m2.start()+100])

# Check all onclick attributes
print('\nAll onclick handlers:')
for onclick in re.findall(r'onclick="([^"]+)"', r.text):
    print(' ', onclick[:80])

# Check for any undefined references
print('\nSearching for problematic patterns...')
# Is the script block properly closed?
script_blocks = list(re.finditer(r'<script[^>]*>(.*?)</script>', r.text, re.DOTALL))
print(f'Total script blocks: {len(script_blocks)}')
for i, b in enumerate(script_blocks):
    content = b.group(1)
    has_toggle = 'toggleChat' in content
    print(f'  Block {i}: len={len(content)}, has toggleChat={has_toggle}, starts_at={b.start()}, ends_at={b.end()}')