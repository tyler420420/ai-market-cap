import re

path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the renderTable row-building section
start = content.find("html+='<tr style")
end = content.find("sortBy('days_left');", start) + len("sortBy('days_left');")
segment = content[start:end]

print(f'Segment length: {len(segment)}')

# Build the new segment by replacing each <td> with <td data-label="...">
# We'll use sequential replacements on specific patterns
replacements = [
    ('<tr style=\\"background:\\'+bg+\'\\"><td><strong>',
     '<tr style=\\"background:\\'+bg+\'\\"><td data-label=\\"Ticker\\"><strong>'),
    ("<td>'+r.company_name.substring(0,35)+(r.company_name.length>35?'...':'')+'</td>",
     "<td data-label=\\"Company\\">'+r.company_name.substring(0,35)+(r.company_name.length>35?'...':'')+'</td>"),
    ("<td><strong style=\\"color:\\'+c+';font-size:1.3em\\">'+r.score+'</strong></td>",
     "<td data-label=\\"Score\\"><strong style=\\"color:\\'+c+'\\">'+r.score+'</strong></td>"),
    ('<td class=earn-cell>',
     '<td data-label=\\"Earnings\\" class=earn-cell>'),
    ('<td style=\\"color:\\'+(r.days_left==0',
     '<td data-label=\\"Days\\" style=\\"color:\\'+(r.days_left==0'),
    # Price - already done
    # 3 Day, 7 Day, 14 Day - already done
    ("<td>'+r.analysts+'</td>",
     "<td data-label=\\"Analysts\\">'+r.analysts+'</td>"),
    ('<td style=\\"color:#00ff88\\">\\'+r.sb+\'</td>',
     '<td data-label=\\"Strong Buy\\" style=\\"color:#00ff88\\">\\'+r.sb+\'</td>'),
    ('<td style=\\"color:#58a6ff\\">\\'+r.buy+\'</td>',
     '<td data-label=\\"Buy\\" style=\\"color:#58a6ff\\">\\'+r.buy+\'</td>'),
    ('<td style=\\"color:#ffcc00\\">\\'+r.hold+\'</td>',
     '<td data-label=\\"Hold\\" style=\\"color:#ffcc00\\">\\'+r.hold+\'</td>'),
    ('<td style=\\"color:#ff6b6b\\">\\'+r.sell+\'</td>',
     '<td data-label=\\"Sell\\" style=\\"color:#ff6b6b\\">\\'+r.sell+\'</td>'),
    ("<td>'+fmtMktcap(r.mktcap)+'</td>",
     "<td data-label=\\"Mkt Cap\\">'+fmtMktcap(r.mktcap)+'</td>"),
    ("<td style=\\'color:#fff\\'>\\'+r.short_int+'%</td>",
     "<td data-label=\\'Shorts\\' style=\\'color:#fff\\'>\\'+r.short_int+'%</td>"),
    ("<td style=\\'color:#fff\\'>\\'+r.iv+'%</td>",
     "<td data-label=\\'IV\\' style=\\'color:#fff\\'>\\'+r.iv+'%</td>"),
    ("<td>\\'+(r.squeeze?",
     "<td data-label=\\"Trend\\">\\'+(r.squeeze?"),
    ("<td>'+newsHtml(r.news)+'</td></tr>",
     "<td data-label=\\"News\\">'+newsHtml(r.news)+'</td></tr>"),
]

changes = 0
for old, new in replacements:
    if old in segment:
        segment = segment.replace(old, new, 1)
        changes += 1
        print(f'OK: {old[:50]}')
    else:
        print(f'MISS: {old[:60]}')

print(f'Changes: {changes}')
if changes >= 10:
    content = content[:start] + segment + content[end:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Written!')
else:
    print('Not enough changes - skipping write')