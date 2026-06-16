path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace using byte-level inspection
# The segment uses actual \" and \' in the file
start = content.find("html+='<tr style")
end = content.find("sortBy('days_left');", start) + len("sortBy('days_left');")
segment = content[start:end]

# Build new segment by replacing each occurrence one by one using index
# Simpler: just replace all occurrences of "<td>" that aren't already "<td data-label"
# But we need to be careful about the order

new_segment = segment

# Pattern replacements using the ACTUAL characters in the file
# The file has: \" for escaped double quote, \' for escaped single quote
# But in the HTML, these become regular " and '

# Use string.replace with the actual characters
# "<td>" in the segment should become "<td data-label=\"X\">"
# But the segment has \" so let me check

# Let me just do a simple test - replace <td><strong><a href with <td data-label="Ticker"><strong><a href
# This should be safe since it's unique

if '<td><strong><a href' in new_segment:
    new_segment = new_segment.replace('<td><strong><a href', '<td data-label="Ticker"><strong><a href', 1)
    print('OK: ticker')
else:
    print('MISS: ticker')

if "<td>'+r.company_name.substring" in new_segment:
    new_segment = new_segment.replace("<td>'+r.company_name.substring", "<td data-label='Company'>'+r.company_name.substring", 1)
    print('OK: company')
else:
    print('MISS: company')

if "<td><strong style=\"color:'+c+';font-size:1.3em\">'+r.score+'</strong></td>" in new_segment:
    new_segment = new_segment.replace("<td><strong style=\"color:'+c+';font-size:1.3em\">'+r.score+'</strong></td>", "<td data-label='Score'><strong style=\"color:'+c+'\">'+r.score+'</strong></td>", 1)
    print('OK: score')
else:
    print('MISS: score')

if "<td class=earn-cell>'+r.earnings_date" in new_segment:
    new_segment = new_segment.replace("<td class=earn-cell>'+r.earnings_date", "<td data-label='Earnings' class=earn-cell>'+r.earnings_date", 1)
    print('OK: earnings')
else:
    print('MISS: earnings')

if "<td style=\"color:'+(r.days_left==0" in new_segment:
    new_segment = new_segment.replace("<td style=\"color:'+(r.days_left==0", "<td data-label='Days' style=\"color:'+(r.days_left==0", 1)
    print('OK: days')
else:
    print('MISS: days')

if "<td>$'+Math.floor(r.price)+'</td>" in new_segment:
    new_segment = new_segment.replace("<td>$'+Math.floor(r.price)+'</td>", "<td data-label='Price'>$'+Math.floor(r.price)+'</td>", 1)
    print('OK: price')
else:
    print('MISS: price')

if "<td><strong>$'+Math.floor(r.pe_target)+'</strong> <span style=\"color:#00ff88\">+'+r.pe_upside+'%</span></td>" in new_segment:
    new_segment = new_segment.replace("<td><strong>$'+Math.floor(r.pe_target)+'</strong> <span style=\"color:#00ff88\">+'+r.pe_upside+'%</span></td>", "<td data-label='3 Day'><strong>$'+Math.floor(r.pe_target)+'</strong> <span style=\"color:#00ff88\">+'+r.pe_upside+'%</span></td>", 1)
    print('OK: 3 day')
else:
    print('MISS: 3 day')

if "<td>$'+Math.floor(r['3d'])+' <span style=\"color:#00ff88\">+'+r['3d_up']+'%</span></td>" in new_segment:
    new_segment = new_segment.replace("<td>$'+Math.floor(r['3d'])+' <span style=\"color:#00ff88\">+'+r['3d_up']+'%</span></td>", "<td data-label='7 Day'>$'+Math.floor(r['3d'])+' <span style=\"color:#00ff88\">+'+r['3d_up']+'%</span></td>", 1)
    print('OK: 7 day')
else:
    print('MISS: 7 day')

if "<td>$'+Math.floor(r['5d'])+' <span style=\"color:#00ff88\">+'+r['5d_up']+'%</span></td>" in new_segment:
    new_segment = new_segment.replace("<td>$'+Math.floor(r['5d'])+' <span style=\"color:#00ff88\">+'+r['5d_up']+'%</span></td>", "<td data-label='14 Day'>$'+Math.floor(r['5d'])+' <span style=\"color:#00ff88\">+'+r['5d_up']+'%</span></td>", 1)
    print('OK: 14 day')
else:
    print('MISS: 14 day')

if "<td>'+r.analysts+'</td>" in new_segment:
    new_segment = new_segment.replace("<td>'+r.analysts+'</td>", "<td data-label='Analysts'>'+r.analysts+'</td>", 1)
    print('OK: analysts')
else:
    print('MISS: analysts')

if "<td style=\"color:#00ff88\">'+r.sb+'</td>" in new_segment:
    new_segment = new_segment.replace("<td style=\"color:#00ff88\">'+r.sb+'</td>", "<td data-label='Strong Buy' style=\"color:#00ff88\">'+r.sb+'</td>", 1)
    print('OK: strong buy')
else:
    print('MISS: strong buy')

if "<td style=\"color:#58a6ff\">'+r.buy+'</td>" in new_segment:
    new_segment = new_segment.replace("<td style=\"color:#58a6ff\">'+r.buy+'</td>", "<td data-label='Buy' style=\"color:#58a6ff\">'+r.buy+'</td>", 1)
    print('OK: buy')
else:
    print('MISS: buy')

if "<td style=\"color:#ffcc00\">'+r.hold+'</td>" in new_segment:
    new_segment = new_segment.replace("<td style=\"color:#ffcc00\">'+r.hold+'</td>", "<td data-label='Hold' style=\"color:#ffcc00\">'+r.hold+'</td>", 1)
    print('OK: hold')
else:
    print('MISS: hold')

if "<td style=\"color:#ff6b6b\">'+r.sell+'</td>" in new_segment:
    new_segment = new_segment.replace("<td style=\"color:#ff6b6b\">'+r.sell+'</td>", "<td data-label='Sell' style=\"color:#ff6b6b\">'+r.sell+'</td>", 1)
    print('OK: sell')
else:
    print('MISS: sell')

if "<td>'+fmtMktcap(r.mktcap)+'</td>" in new_segment:
    new_segment = new_segment.replace("<td>'+fmtMktcap(r.mktcap)+'</td>", "<td data-label='Mkt Cap'>'+fmtMktcap(r.mktcap)+'</td>", 1)
    print('OK: mkt cap')
else:
    print('MISS: mkt cap')

if "<td style='color:#fff'>'+r.short_int+'%</td>" in new_segment:
    new_segment = new_segment.replace("<td style='color:#fff'>'+r.short_int+'%</td>", "<td data-label='Shorts' style='color:#fff'>'+r.short_int+'%</td>", 1)
    print('OK: shorts')
else:
    print('MISS: shorts')

if "<td style='color:#fff'>'+r.iv+'%</td>" in new_segment:
    new_segment = new_segment.replace("<td style='color:#fff'>'+r.iv+'%</td>", "<td data-label='IV' style='color:#fff'>'+r.iv+'%</td>", 1)
    print('OK: iv')
else:
    print('MISS: iv')

if "<td>+(r.squeeze?" in new_segment:
    new_segment = new_segment.replace("<td>+(r.squeeze?", "<td data-label='Trend'>+(r.squeeze?", 1)
    print('OK: trend')
else:
    print('MISS: trend')

if "<td>'+newsHtml(r.news)+'</td></tr>" in new_segment:
    new_segment = new_segment.replace("<td>'+newsHtml(r.news)+'</td></tr>", "<td data-label='News'>'+newsHtml(r.news)+'</td></tr>", 1)
    print('OK: news')
else:
    print('MISS: news')

# Write back
content = content[:start] + new_segment + content[end:]
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('\nWritten!')