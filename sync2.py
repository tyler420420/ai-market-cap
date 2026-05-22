with open(r'C:\Users\Tyler_AI\.mavis\sessions\mvs_41a119d03ae849d59a2cdecd57e77d10\workspace\ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Fix th CSS directly
c = c.replace(
    'th{background:#1f2937;padding:10px 12px;text-align:left;font-size:0.78em;color:#8b949e;text-transform:uppercase;border-bottom:2px solid #30363d;cursor:pointer;user-select:none;white-space:nowrap}',
    'th{background:#1f2937;padding:10px 12px;text-align:left;font-size:0.78em;color:#8b949e;text-transform:uppercase;border-bottom:2px solid #30363d;cursor:pointer;user-select:none;white-space:nowrap}th:hover{color:#c9d1d9}thead th{color:#fff!important}thead th:hover{color:#8b949e}thead tr{border-bottom:2px solid #3fb950;box-shadow:0 2px 10px rgba(63,185,80,0.5)}'
)

# Fix headers
c = c.replace(
    "('Next Report','earnings_date'), ('Days Left','days_left'), ('Price','price'),\n        ('PE Target','pe_target'), ('3-Day Momentum','3d'), ('5-Day Momentum','5d'),\n        ('# of Analyst Signals','analysts'), ('Strong Buy','sb')",
    "('Next Earnings','earnings_date'), ('Days<br>Left','days_left'), ('Current<br>Price','price'),\n        ('Post Earnings<br>Target','pe_target'), ('Great Earnings Report','3d'), ('Excellent Earnings Report','5d'),\n        ('Analyst<br>Reports','analysts'), ('S-BUY','sb')"
)

# Fix green divider
c = c.replace(
    "td{padding:18px 12px;border-bottom:1px solid #30363d;font-size:0.88em}tr{height:54px}tr:hover{background:#1c2128}",
    "td{padding:10px 10px;border-bottom:1px solid #30363d;font-size:0.88em;color:#fff}td:nth-child(6){border-right:2px solid #3fb950;box-shadow:1px 0 8px rgba(63,185,80,0.5)}tr{height:auto}tr:hover{background:#1c2128}"
)

# Fix 3D/5D columns format
c = c.replace(
    "static_rows += '<td>$' + str(r['3d']) + ' | +' + str(r['3d_up']) + '%</td>'",
    "static_rows += '<td>$' + str(r['3d']) + '<br><span style=\"color:#00ff88\">+' + str(r['3d_up']) + '%</span></td>'"
)
c = c.replace(
    "static_rows += '<td>$' + str(r['5d']) + ' | +' + str(r['5d_up']) + '%</td>'",
    "static_rows += '<td>$' + str(r['5d']) + '<br><span style=\"color:#00ff88\">+' + str(r['5d_up']) + '%</span></td>'"
)

with open(r'C:\Users\Tyler_AI\.mavis\sessions\mvs_41a119d03ae849d59a2cdecd57e77d10\workspace\ai_earnings_scanner.py', 'w', encoding='utf-8') as f:
    f.write(c)
print('Done')