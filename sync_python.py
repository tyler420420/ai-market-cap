with open(r'C:\Users\Tyler_AI\.mavis\sessions\mvs_41a119d03ae849d59a2cdecd57e77d10\workspace\ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Change .ticker-price from grey to white
c = c.replace('.ticker-price{color:#c9d1d9}', '.ticker-price{color:#fff}')

# 2. Add td white color and bold prices
c = c.replace(
    'td{padding:18px 12px;border-bottom:1px solid #30363d;font-size:0.88em}tr{height:54px}tr:hover{background:#1c2128}',
    'td{padding:10px 10px;border-bottom:1px solid #30363d;font-size:0.88em;color:#fff}td:nth-child(6){border-right:2px solid #3fb950;box-shadow:1px 0 8px rgba(63,185,80,0.5)}tr{height:auto}tr:hover{background:#1c2128}'
)

# 3. Update th CSS - white headers, hover grey
c = c.replace(
    "th{background:#1f2937;padding:10px 12px;text-align:left;font-size:0.78em;color:#8b949e;text-transform:uppercase;border-bottom:2px solid #30363d;cursor:pointer;user-select:none;white-space:nowrap}th:hover{color:#c9d1d9}",
    "thead th{color:#fff!important}thead th:hover{color:#8b949e}thead tr{border-bottom:2px solid #3fb950;box-shadow:0 2px 10px rgba(63,185,80,0.5)}"
)

# 4. Update headers list with new names
old_headers = "('Next Report','earnings_date'), ('Days Left','days_left'), ('Price','price'), ('PE Target','pe_target'), ('3-Day Momentum','3d'), ('5-Day Momentum','5d'), ('# of Analyst Signals','analysts'), ('Strong Buy','sb')"
new_headers = "('Next Earnings','earnings_date'), ('Days<br>Left','days_left'), ('Current<br>Price','price'), ('Post Earnings<br>Target','pe_target'), ('Great Earnings Report','3d'), ('Excellent Earnings Report','5d'), ('Analyst<br>Reports','analysts'), ('S-BUY','sb')"
c = c.replace(old_headers, new_headers)

# 5. Update static rows to have bold price
c = c.replace(
    "static_rows += '<td>$' + str(r['price']) + '</td>'",
    "static_rows += '<td style=\"font-weight:bold\">$' + str(r['price']) + '</td>'"
)

# 6. Update PE Target to have price on one line, percent on next (in static rows)
c = c.replace(
    "static_rows += '<td>$' + str(r['pe_target']) + ' | +' + str(r['pe_upside']) + '%</td>'",
    "static_rows += '<td style=\"font-weight:bold\">$' + str(r['pe_target']) + '<br><span style=\"color:#00ff88\">+' + str(r['pe_upside']) + '%</span></td>'"
)

# 7. Update 3D and 5D columns similarly
c = c.replace(
    "static_rows += '<td>$' + str(r['3d']) + ' | +' + str(r['3d_up']) + '%</td>'",
    "static_rows += '<td>$' + str(r['3d']) + '<br><span style=\"color:#00ff88\">+' + str(r['3d_up']) + '%</span></td>'"
)
c = c.replace(
    "static_rows += '<td>$' + str(r['5d']) + ' | +' + str(r['5d_up']) + '%</td>'",
    "static_rows += '<td>$' + str(r['5d']) + '<br><span style=\"color:#00ff88\">+' + str(r['5d_up']) + '%</span></td>'"
)

# 8. Gold featured trade banner
c = c.replace(
    ".pick-banner{background:linear-gradient(135deg,#1a2a1a,#162016);border:1px solid #2ea043",
    ".pick-banner{background:linear-gradient(135deg,#2a1a00,#ffd700);border:2px solid #ffd700"
)

# 9. Add feat-glow animation
old_end = "z-index:9999;transition:background .2s}'"
new_end = "z-index:9999;transition:background .2s}@keyframes feat-glow{0%,100%{box-shadow:0 0 8px rgba(255,215,0,.5)}50%{box-shadow:0 0 25px rgba(255,215,0,.9)}}@keyframes sb-glow{0%,100%{box-shadow:0 0 4px rgba(63,185,80,.3)}50%{box-shadow:0 0 10px rgba(63,185,80,.6)}}tr[style*=\"rgba(0,255,136,0.12)\"]{animation:sb-glow 2.5s ease-in-out infinite;border-left:3px solid #3fb950}.pick-banner{animation:feat-glow 2s ease-in-out infinite}"
c = c.replace(old_end, new_end)

# 10. Fix description color in HTML generation
c = c.replace(
    "html += '<div class=desc>Pre-earnings momentum scanner for AI/AI-niche sector | Entry 1-14 days before | Exit 1-5 days after beat</div></div>'",
    "html += '<div class=desc>Pre-earnings momentum scanner for AI/AI-niche sector | Entry 1-14 days before | Exit 1-5 days after beat | Updated: ' + timestamp + '</div></div>'"
)

# 11. Update pick banner style inline
c = c.replace(
    "html += '<div class=pick-banner style=\"background:linear-gradient(135deg,#0d2b1a,#162016);border:1px solid #2ea043",
    "html += '<div class=pick-banner style=\"background:linear-gradient(135deg,#2a1a00,#ffd700);border:2px solid #ffd700"
)

with open(r'C:\Users\Tyler_AI\.mavis\sessions\mvs_41a119d03ae849d59a2cdecd57e77d10\workspace\ai_earnings_scanner.py', 'w', encoding='utf-8') as f:
    f.write(c)

print('All CSS changes applied to Python script')
print('Checking for issues...')

# Verify key changes
with open(r'C:\Users\Tyler_AI\.mavis\sessions\mvs_41a119d03ae849d59a2cdecd57e77d10\workspace\ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    c = f.read()

checks = [
    ('.ticker-price{color:#fff}', 'ticker price white'),
    ('color:#fff!important', 'th headers white'),
    ('thead th{', 'thead th selector'),
    ('font-weight:bold">$', 'price bold'),
    ('Post Earnings<br>Target', 'PE Target renamed'),
    ('Great Earnings Report', '3D renamed'),
    ('Excellent Earnings Report', '5D renamed'),
    ('border-right:2px solid #3fb950', 'green divider'),
    ('border-bottom:2px solid #3fb950', 'green header line'),
    ('#ffd700', 'gold banner'),
]

for pattern, desc in checks:
    if pattern in c:
        print(f'  OK: {desc}')
    else:
        print(f'  MISSING: {desc} - {pattern}')