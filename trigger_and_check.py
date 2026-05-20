import requests, secrets, time, re

token = secrets.token_hex(32)
expires = int(time.time()) + 86400
s = requests.Session()
s.cookies.set('scanner_session', f'{token}|{expires}')

print('Triggering scan...')
r = s.post('https://aismarketcap.com/run', timeout=5)
print('Triggered:', r.status_code)

print('Waiting for scan to complete (up to 2 min)...')
for i in range(24):
    time.sleep(5)
    r2 = s.get('https://aismarketcap.com/status', timeout=5)
    data = r2.json()
    state = data.get('scan_state', 'unknown')
    print(f'{(i+1)*5}s: scan_state={state}')
    if state == 'done':
        print('Scan complete!')
        # Check the new scan file
        r3 = s.get('https://aismarketcap.com/scan/latest', timeout=10)
        print(f'Scan file: {len(r3.text)} bytes')
        m = re.search(r'var rowsData=(.*?);', r3.text, re.DOTALL)
        if m:
            print(f'rowsData: {m.group(1)[:100]}')
        break
else:
    print('Timeout!')

# Also check scanner page
r4 = s.get('https://aismarketcap.com/scanner', timeout=10)
print(f'\nScanner page: {len(r4.text)} bytes')
m2 = re.search(r'var rowsData=(.*?);', r4.text, re.DOTALL)
if m2:
    print(f'Scanner rowsData: {m2.group(1)[:100]}')