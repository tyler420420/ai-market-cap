path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_today.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix with actual patterns from HTML
replacements = [
    # Ticker (uses \" in HTML)
    ("html+=\\'<tr style=\"background:\\'+bg+\\'\\"><td><strong><a href=\"https://finance.yahoo.com/quote/\\'+r.ticker+\\'\\" target=\"_blank\" style=\"color:#66b2ff\">\\'+r.ticker+\\'</a></strong></td>\\';",
     "html+=\\'<tr style=\"background:\\'+bg+\\'\\"><td data-label=\"Ticker\"><strong><a href=\"https://finance.yahoo.com/quote/\\'+r.ticker+\\'\\" target=\"_blank\" style=\"color:#66b2ff\">\\'+r.ticker+\\'</a></strong></td>\\';"),
    # 3 Day Target
    ("html+=\\'<td><strong>$\\'+Math.floor(r.pe_target)+\\'</strong> <span style=\"color:#00ff88\">+\\'+r.pe_upside+\\'%</span></td>\\';",
     "html+=\\'<td data-label=\"3 Day\"><strong>$\\'+Math.floor(r.pe_target)+\\'</strong> <span style=\"color:#00ff88\">+\\'+r.pe_upside+\\'%</span></td>\\';"),
    # 7 Day
    ("html+=\\'<td>$\\'+Math.floor(r['3d'])+\\' <span style=\"color:#00ff88\">+\\'+r['3d_up']+\\'%</span></td>\\';",
     "html+=\\'<td data-label=\"7 Day\">$\\'+Math.floor(r['3d'])+\\' <span style=\"color:#00ff88\">+\\'+r['3d_up']+\\'%</span></td>\\';"),
    # 14 Day
    ("html+=\\'<td>$\\'+Math.floor(r['5d'])+\\' <span style=\"color:#00ff88\">+\\'+r['5d_up']+\\'%</span></td>\\';",
     "html+=\\'<td data-label=\"14 Day\">$\\'+Math.floor(r['5d'])+\\' <span style=\"color:#00ff88\">+\\'+r['5d_up']+\\'%</span></td>\\';"),
    # Shorts
    ("html+=\\'<td style=\\'color:#fff\\'>\\'+r.short_int+'%</td>\\';",
     "html+=\\'<td data-label=\\'Shorts\\' style=\\'color:#fff\\'>\\'+r.short_int+'%</td>\\';"),
    # IV
    ("html+=\\'<td style=\\'color:#fff\\'>\\'+r.iv+'%</td>\\';",
     "html+=\\'<td data-label=\\'IV\\' style=\\'color:#fff\\'>\\'+r.iv+'%</td>\\';"),
    # Trend/Squeeze
    ("html+=\\'<td>+(r.squeeze?",
     "html+=\\'<td data-label=\"Trend\">+(r.squeeze?"),
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
if changes >= 5:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Written!')