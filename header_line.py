with open(r'C:\Users\Tyler_AI\.mavis\sessions\mvs_41a119d03ae849d59a2cdecd57e77d10\workspace\ai_earnings_tight.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Add green glowing line under the header row
old = 'thead th{color:#fff!important}thead th:hover{color:#8b949e}'
new = 'thead th{color:#fff!important}thead th:hover{color:#8b949e}thead tr{border-bottom:2px solid #3fb950;box-shadow:0 2px 10px rgba(63,185,80,0.5)}'
c = c.replace(old, new, 1)

with open(r'C:\Users\Tyler_AI\.mavis\sessions\mvs_41a119d03ae849d59a2cdecd57e77d10\workspace\ai_earnings_tight.html', 'w', encoding='utf-8') as f:
    f.write(c)
print('Done')