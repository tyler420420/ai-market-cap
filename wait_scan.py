import requests, secrets, time

token = secrets.token_hex(32)
expires = int(time.time()) + 86400
s = requests.Session()
s.cookies.set('scanner_session', f'{token}|{expires}')

print('Triggering scan...')
r = s.post('https://aismarketcap.com/run', timeout=5)
print('Trigger:', r.status_code, r.text)

print('\nPolling every 5s...')
for i in range(24):
    time.sleep(5)
    r2 = s.get('https://aismarketcap.com/status', timeout=5)
    data = r2.json()
    state = data.get('scan_state', 'unknown')
    refresh = data.get('refresh_state', 'unknown')
    print(f'{(i+1)*5}s: scan={state}, refresh={refresh}')
    if state == 'done':
        print('\nSCAN DONE! Checking file...')
        r3 = s.get('https://aismarketcap.com/scan/latest', timeout=10)
        print(f'Scan file: {len(r3.text)} bytes, status={r3.status_code}')
        # Check rowsData
        if 'rowsData' in r3.text:
            import re
            m = re.search(r'var rowsData=(.*?);', r3.text, re.DOTALL)
            if m:
                print(f'rowsData: {m.group(1)[:50]}')
        break
else:
    print('Timeout - scan still running after 2 min')