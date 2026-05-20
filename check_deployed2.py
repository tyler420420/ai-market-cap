import requests, secrets, time, re

token = secrets.token_hex(32)
expires = int(time.time()) + 86400
s = requests.Session()
s.cookies.set('scanner_session', f'{token}|{expires}')
r = s.get('https://aismarketcap.com/scanner', timeout=15)

print(f'Page size: {len(r.text)} bytes')

# Check what Railway has as latest file
from pathlib import Path
workspace = Path('.')
html_files = sorted(workspace.glob('ai_earnings_57day_*.html'), key=lambda f: f.stat().st_mtime, reverse=True)
print(f'Local latest: {html_files[0].name} ({html_files[0].stat().st_size} bytes)')

# Find rowsData count
m = re.search(r'var rowsData=(.*?);', r.text, re.DOTALL)
if m:
    data = m.group(1)
    print(f'rowsData length: {len(data)} chars')
    if data.strip() == '[]':
        print('ROWS DATA IS EMPTY!')
    else:
        try:
            import json
            parsed = json.loads(data)
            print(f'rowsData has {len(parsed)} stocks')
        except:
            print('rowsData is not valid JSON')

# Check scan script block
scan_script_pos = r.text.find('scanBtn=document.getElementById')
if scan_script_pos >= 0:
    print(f'\nScan script at pos {scan_script_pos}')
    print(r.text[scan_script_pos:scan_script_pos+300])