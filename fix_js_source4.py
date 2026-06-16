path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find("html+='<tr style")
end = content.find("sortBy('days_left');", start) + len("sortBy('days_left');")
segment = content[start:end]

print(f'Segment length: {len(segment)}')

# Define replacements as tuples of (old, new) with proper escaping
# Use the actual characters from the file
replacements = []

# 1. Ticker
replacements.append(('<td><strong><a href', '<td data-label="Ticker"><strong><a href'))

# 2. Company
replacements.append(("<td>'+r.company_name.substring", '<td data-label="Company">'+r.company_name.substring))

# 3. Score
replacements.append(('<td><strong style="color:\'+c+\';font-size:1.3em">\'+r.score+\'</strong></td>', '<td data-label="Score"><strong style="color:\'+c+\'">\'+r.score+\'</strong></td>'))

# 4. Earnings
replacements.append(('<td class=earn-cell>\'+r.earnings_date', '<td data-label="Earnings" class=earn-cell>\'+r.earnings_date'))

# 5. Days
replacements.append(('<td style="color:\'+(r.days_left==0', '<td data-label="Days" style="color:\'+(r.days_left==0'))

# 6. Price
replacements.append(("<td>$'+Math.floor(r.price)+'</td>", '<td data-label="Price">$'+Math.floor(r.price)+'</td>'))

# 7. 3 Day Target
replacements.append(("<td><strong>$'+Math.floor(r.pe_target)+'</strong> <span style=\"color:#00ff88\">+'+r.pe_upside+'%</span></td>", '<td data-label="3 Day"><strong>$'+Math.floor(r.pe_target)+'</strong> <span style="color:#00ff88">+'+r.pe_upside+'%</span></td>'))

# 8. 7 Day
replacements.append(("<td>$'+Math.floor(r['3d'])+' <span style=\"color:#00ff88\">+'+r['3d_up']+'%</span></td>", '<td data-label="7 Day">$'+Math.floor(r['3d'])+' <span style="color:#00ff88">+'+r['3d_up']+'%</span></td>'))

# 9. 14 Day
replacements.append(("<td>$'+Math.floor(r['5d'])+' <span style=\"color:#00ff88\">+'+r['5d_up']+'%</span></td>", '<td data-label="14 Day">$'+Math.floor(r['5d'])+' <span style="color:#00ff88">+'+r['5d_up']+'%</span></td>'))

# 10. Analysts
replacements.append(("<td>'+r.analysts+'</td>", '<td data-label="Analysts">'+r.analysts+'</td>'))

# 11. Strong Buy
replacements.append(("<td style=\"color:#00ff88\">'+r.sb+'</td>", '<td data-label="Strong Buy" style="color:#00ff88">'+r.sb+'</td>'))

# 12. Buy
replacements.append(("<td style=\"color:#58a6ff\">'+r.buy+'</td>", '<td data-label="Buy" style="color:#58a6ff">'+r.buy+'</td>'))

# 13. Hold
replacements.append(("<td style=\"color:#ffcc00\">'+r.hold+'</td>", '<td data-label="Hold" style="color:#ffcc00">'+r.hold+'</td>'))

# 14. Sell
replacements.append(("<td style=\"color:#ff6b6b\">'+r.sell+'</td>", '<td data-label="Sell" style="color:#ff6b6b">'+r.sell+'</td>'))

# 15. Mkt Cap
replacements.append(("<td>'+fmtMktcap(r.mktcap)+'</td>", '<td data-label="Mkt Cap">'+fmtMktcap(r.mktcap)+'</td>'))

# 16. Shorts
replacements.append(("<td style='color:#fff'>'+r.short_int+'%</td>", "<td data-label='Shorts' style='color:#fff'>'+r.short_int+'%</td>"))

# 17. IV
replacements.append(("<td style='color:#fff'>'+r.iv+'%</td>", "<td data-label='IV' style='color:#fff'>'+r.iv+'%</td>"))

# 18. Trend/Squeeze
replacements.append(("<td>+(r.squeeze?", '<td data-label="Trend">+(r.squeeze?'))

# 19. News
replacements.append(("<td>'+newsHtml(r.news)+'</td></tr>", "<td data-label='News'>'+newsHtml(r.news)+'</td></tr>"))

changes = 0
for old, new in replacements:
    if old in segment:
        segment = segment.replace(old, new, 1)
        changes += 1
        print(f'OK: {old[:40]}')
    else:
        print(f'MISS: {old[:50]}')

print(f'\nTotal: {changes}/{len(replacements)}')
if changes >= 15:
    content = content[:start] + segment + content[end:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Written!')
else:
    print('Not enough - skipping write')