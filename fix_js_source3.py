path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find("html+='<tr style")
end = content.find("sortBy('days_left');", start) + len("sortBy('days_left');")
segment = content[start:end]

print(f'Segment length: {len(segment)}')

# Use raw strings for replacements
replacements = [
    (r"<td><strong><a href", r'<td data-label="Ticker"><strong><a href'),
    (r"<td>'+r.company_name.substring", r'<td data-label="Company">'+r.company_name.substring'),
    (r"<td><strong style=\"color:'+c+';font-size:1.3em\">'+r.score+'</strong></td>", r'<td data-label="Score"><strong style="color:\'+c+\'">'+r.score+'</strong></td>'),
    (r"<td class=earn-cell>'+r.earnings_date", r'<td data-label="Earnings" class=earn-cell>'+r.earnings_date),
    (r"<td style=\"color:'+(r.days_left==0", r'<td data-label="Days" style="color:\'+(r.days_left==0'),
    (r"<td>$'+Math.floor(r.price)+'</td>", r'<td data-label="Price">$'+Math.floor(r.price)+'</td>'),
    (r"<td><strong>$'+Math.floor(r.pe_target)+'</strong> <span style=\"color:#00ff88\">+'+r.pe_upside+'%</span></td>", r'<td data-label="3 Day"><strong>$'+Math.floor(r.pe_target)+'</strong> <span style="color:#00ff88">+'+r.pe_upside+'%</span></td>'),
    (r"<td>$'+Math.floor(r['3d'])+' <span style=\"color:#00ff88\">+'+r['3d_up']+'%</span></td>", r'<td data-label="7 Day">$'+Math.floor(r['3d'])+' <span style="color:#00ff88">+'+r['3d_up']+'%</span></td>'),
    (r"<td>$'+Math.floor(r['5d'])+' <span style=\"color:#00ff88\">+'+r['5d_up']+'%</span></td>", r'<td data-label="14 Day">$'+Math.floor(r['5d'])+' <span style="color:#00ff88">+'+r['5d_up']+'%</span></td>'),
    (r"<td>'+r.analysts+'</td>", r'<td data-label="Analysts">'+r.analysts+'</td>'),
    (r"<td style=\"color:#00ff88\">'+r.sb+'</td>", r'<td data-label="Strong Buy" style="color:#00ff88">'+r.sb+'</td>'),
    (r"<td style=\"color:#58a6ff\">'+r.buy+'</td>", r'<td data-label="Buy" style="color:#58a6ff">'+r.buy+'</td>'),
    (r"<td style=\"color:#ffcc00\">'+r.hold+'</td>", r'<td data-label="Hold" style="color:#ffcc00">'+r.hold+'</td>'),
    (r"<td style=\"color:#ff6b6b\">'+r.sell+'</td>", r'<td data-label="Sell" style="color:#ff6b6b">'+r.sell+'</td>'),
    (r"<td>'+fmtMktcap(r.mktcap)+'</td>", r'<td data-label="Mkt Cap">'+fmtMktcap(r.mktcap)+'</td>'),
    (r"<td style='color:#fff'>'+r.short_int+'%</td>", r"<td data-label='Shorts' style='color:#fff'>'+r.short_int+'%</td>"),
    (r"<td style='color:#fff'>'+r.iv+'%</td>", r"<td data-label='IV' style='color:#fff'>'+r.iv+'%</td>"),
    (r"<td>+(r.squeeze?", r'<td data-label="Trend">+(r.squeeze?'),
    (r"<td>'+newsHtml(r.news)+'</td></tr>", r"<td data-label='News'>'+newsHtml(r.news)+'</td></tr>"),
]

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