with open(r'C:\Users\Tyler_AI\.mavis\sessions\mvs_41a119d03ae849d59a2cdecd57e77d10\workspace\ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    c = f.read()

checks = [
    ('.desc{color:#fff', 'Description white'),
    ('.ticker-price{color:#fff}', 'Ticker price white'),
    ('thead th{color:#fff!important}', 'Header th white with !important'),
    ('thead tr{border-bottom:2px solid #3fb950', 'Green header line'),
    ('td:nth-child(6){border-right:2px solid #3fb950', 'Green price divider'),
    ('font-weight:bold">$', 'Bold price in static rows'),
    ('Post Earnings<br>Target', 'PE Target renamed'),
    ('Great Earnings Report', '3D renamed'),
    ('Excellent Earnings Report', '5D renamed'),
    ('Analyst<br>Reports', 'Analyst renamed'),
    ('S-BUY', 'Strong Buy renamed'),
    ('Days<br>Left', 'Days Left broken'),
    ('Current<br>Price', 'Price renamed'),
    ('#ffd700', 'Gold banner'),
    ('feat-glow', 'Banner glow animation'),
    ('sb-glow', 'Row glow animation'),
    ('<br><span style="color:#00ff88">+', '3D/5D have br tag'),
]

print('Checking Python script:')
all_ok = True
for pattern, desc in checks:
    if pattern in c:
        print(f'  OK: {desc}')
    else:
        print(f'  MISSING: {desc}')
        all_ok = False

if all_ok:
    print('\nAll changes synced! Ready to push.')