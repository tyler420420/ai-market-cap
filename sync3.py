with open(r'C:\Users\Tyler_AI\.mavis\sessions\mvs_41a119d03ae849d59a2cdecd57e77d10\workspace\ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Show exact line 395
lines = c.split('\n')
for i, line in enumerate(lines):
    if 'td{padding' in line and '18px' in line:
        print(f'Line {i+1}: {repr(line)}')
    if 'th{background' in line:
        print(f'Line {i+1}: {repr(line)}')

# Fix th CSS - find exact string
old_th = "th{background:#1f2937;padding:10px 12px;text-align:left;font-size:0.78em;color:#8b949e;text-transform:uppercase;border-bottom:2px solid #30363d;cursor:pointer;user-select:none;white-space:nowrap}"
new_th = old_th + "th:hover{color:#c9d1d9}thead th{color:#fff!important}thead th:hover{color:#8b949e}thead tr{border-bottom:2px solid #3fb950;box-shadow:0 2px 10px rgba(63,185,80,0.5)}"
if old_th in c:
    c = c.replace(old_th, new_th, 1)
    print('Fixed th CSS')
else:
    print('th CSS not found exactly')

# Fix td CSS
old_td = "td{padding:18px 12px;border-bottom:1px solid #30363d;font-size:0.88em}tr{height:54px}tr:hover{background:#1c2128}"
new_td = "td{padding:10px 10px;border-bottom:1px solid #30363d;font-size:0.88em;color:#fff}td:nth-child(6){border-right:2px solid #3fb950;box-shadow:1px 0 8px rgba(63,185,80,0.5)}tr{height:auto}tr:hover{background:#1c2128}"
if old_td in c:
    c = c.replace(old_td, new_td, 1)
    print('Fixed td CSS')
else:
    print('td CSS not found exactly, searching...')
    idx = c.find("td{padding:18px")
    if idx >= 0:
        print('Found at:', repr(c[idx:idx+200]))

with open(r'C:\Users\Tyler_AI\.mavis\sessions\mvs_41a119d03ae849d59a2cdecd57e77d10\workspace\ai_earnings_scanner.py', 'w', encoding='utf-8') as f:
    f.write(c)