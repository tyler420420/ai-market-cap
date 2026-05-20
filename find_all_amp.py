import requests, secrets, time, re

token = secrets.token_hex(32)
expires = int(time.time()) + 86400
s = requests.Session()
s.cookies.set('scanner_session', f'{token}|{expires}')
r = s.get('https://aismarketcap.com/scanner', timeout=15)

print('Status:', r.status_code)

# Find ALL &amp; in the response
positions = []
for m in re.finditer(r'&amp;', r.text):
    positions.append(m.start())

print(f'Total &amp; occurrences: {len(positions)}')

for pos in positions:
    ctx = r.text[max(0,pos-40):pos+60]
    print(f'\nAt pos {pos}:')
    print(repr(ctx))