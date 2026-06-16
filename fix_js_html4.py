path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_today.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# The actual HTML uses \" in JS strings (not \\")
replacements = [
    # Ticker - actual pattern in HTML
    ("<td><strong><a href=\"https://finance.yahoo.com/quote/\'+r.ticker+\'\"",
     "<td data-label=\"Ticker\"><strong><a href=\"https://finance.yahoo.com/quote/\'+r.ticker+\'\""),
    # 3 Day Target - check actual pattern
    ("<td><strong>$'+Math.floor(r.pe_target)+'</strong> <span style=\"color:#00ff88\">+'+r.pe_upside+'%</span></td>",
     "<td data-label=\"3 Day\"><strong>$'+Math.floor(r.pe_target)+'</strong> <span style=\"color:#00ff88\">+'+r.pe_upside+'%</span></td>"),
    # 7 Day
    ("<td>$'+Math.floor(r['3d'])+' <span style=\"color:#00ff88\">+'+r['3d_up']+'%</span></td>",
     "<td data-label=\"7 Day\">$'+Math.floor(r['3d'])+' <span style=\"color:#00ff88\">+'+r['3d_up']+'%</span></td>"),
    # 14 Day
    ("<td>$'+Math.floor(r['5d'])+' <span style=\"color:#00ff88\">+'+r['5d_up']+'%</span></td>",
     "<td data-label=\"14 Day\">$'+Math.floor(r['5d'])+' <span style=\"color:#00ff88\">+'+r['5d_up']+'%</span></td>"),
    # Shorts - actual pattern
    ("<td style='color:#fff'>'+r.short_int+'%</td>",
     "<td data-label='Shorts' style='color:#fff'>'+r.short_int+'%</td>"),
    # IV
    ("<td style='color:#fff'>'+r.iv+'%</td>",
     "<td data-label='IV' style='color:#fff'>'+r.iv+'%</td>"),
    # Trend/Squeeze
    ("<td>+(r.squeeze?",
     "<td data-label=\"Trend\">+(r.squeeze?"),
]

changes = 0
for old, new in replacements:
    if old in content:
        content = content.replace(old, new, 1)
        changes += 1
        print(f'OK: {old[:60]}')
    else:
        print(f'MISS: {old[:60]}')

print(f'\nTotal: {changes}/{len(replacements)}')
if changes >= 4:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Written!')