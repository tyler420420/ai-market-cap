path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find("html+='<tr style")
end = content.find("sortBy('days_left');", start) + len("sortBy('days_left');")
segment = content[start:end]

print(f'Segment length: {len(segment)}')

# Replace based on patterns found in the segment
# Just look for <td> that don't have data-label yet
import re

# Count how many td without data-label
tds = re.findall(r"<td([^>]*)>", segment)
print(f'Total td in segment: {len(tds)}')
without = [t for t in tds if 'data-label' not in t]
print(f'TD without data-label: {len(without)}')
for t in without[:5]:
    print(f'  attr: {t[:50]}')

# Do simple sequential replacements
# 1. First td (ticker)
old1 = "<td><strong><a href"
new1 = '<td data-label="Ticker"><strong><a href'
if old1 in segment:
    segment = segment.replace(old1, new1, 1)
    print("OK: ticker")
else:
    print("MISS: ticker")

# 2. Company
old2 = "<td>'+r.company_name.substring"
new2 = '<td data-label="Company">'+r.company_name.substring
if old2 in segment:
    segment = segment.replace(old2, new2, 1)
    print("OK: company")
else:
    print("MISS: company")

# 3. Score
old3 = "<td><strong style=\"color:'+c+';font-size:1.3em\">'+r.score+'</strong></td>"
new3 = '<td data-label="Score"><strong style="color:\'+c+\'">'+r.score+'</strong></td>'
if old3 in segment:
    segment = segment.replace(old3, new3, 1)
    print("OK: score")
else:
    print("MISS: score")

# 4. Earnings
old4 = "<td class=earn-cell>'+r.earnings_date"
new4 = '<td data-label="Earnings" class=earn-cell>'+r.earnings_date
if old4 in segment:
    segment = segment.replace(old4, new4, 1)
    print("OK: earnings")
else:
    print("MISS: earnings")

# 5. Days
old5 = "<td style=\"color:'+(r.days_left==0"
new5 = '<td data-label="Days" style="color:\'+(r.days_left==0'
if old5 in segment:
    segment = segment.replace(old5, new5, 1)
    print("OK: days")
else:
    print("MISS: days")

# 6. Price
old6 = "<td>$'+Math.floor(r.price)+'</td>"
new6 = '<td data-label="Price">$'+Math.floor(r.price)+'</td>'
if old6 in segment:
    segment = segment.replace(old6, new6, 1)
    print("OK: price")
else:
    print("MISS: price")

# 7. 3 Day Target
old7 = "<td><strong>$'+Math.floor(r.pe_target)+'</strong> <span style=\"color:#00ff88\">+'+r.pe_upside+'%</span></td>"
new7 = '<td data-label="3 Day"><strong>$'+Math.floor(r.pe_target)+'</strong> <span style="color:#00ff88">+'+r.pe_upside+'%</span></td>'
if old7 in segment:
    segment = segment.replace(old7, new7, 1)
    print("OK: 3 day")
else:
    print("MISS: 3 day")

# 8. 7 Day
old8 = "<td>$'+Math.floor(r['3d'])+' <span style=\"color:#00ff88\">+'+r['3d_up']+'%</span></td>"
new8 = '<td data-label="7 Day">$'+Math.floor(r['3d'])+' <span style="color:#00ff88">+'+r['3d_up']+'%</span></td>'
if old8 in segment:
    segment = segment.replace(old8, new8, 1)
    print("OK: 7 day")
else:
    print("MISS: 7 day")

# 9. 14 Day
old9 = "<td>$'+Math.floor(r['5d'])+' <span style=\"color:#00ff88\">+'+r['5d_up']+'%</span></td>"
new9 = '<td data-label="14 Day">$'+Math.floor(r['5d'])+' <span style="color:#00ff88">+'+r['5d_up']+'%</span></td>'
if old9 in segment:
    segment = segment.replace(old9, new9, 1)
    print("OK: 14 day")
else:
    print("MISS: 14 day")

# 10. Analysts
old10 = "<td>'+r.analysts+'</td>"
new10 = '<td data-label="Analysts">'+r.analysts+'</td>'
if old10 in segment:
    segment = segment.replace(old10, new10, 1)
    print("OK: analysts")
else:
    print("MISS: analysts")

# 11. Strong Buy
old11 = "<td style=\"color:#00ff88\">'+r.sb+'</td>"
new11 = '<td data-label="Strong Buy" style="color:#00ff88">'+r.sb+'</td>'
if old11 in segment:
    segment = segment.replace(old11, new11, 1)
    print("OK: strong buy")
else:
    print("MISS: strong buy")

# 12. Buy
old12 = "<td style=\"color:#58a6ff\">'+r.buy+'</td>"
new12 = '<td data-label="Buy" style="color:#58a6ff">'+r.buy+'</td>'
if old12 in segment:
    segment = segment.replace(old12, new12, 1)
    print("OK: buy")
else:
    print("MISS: buy")

# 13. Hold
old13 = "<td style=\"color:#ffcc00\">'+r.hold+'</td>"
new13 = '<td data-label="Hold" style="color:#ffcc00">'+r.hold+'</td>'
if old13 in segment:
    segment = segment.replace(old13, new13, 1)
    print("OK: hold")
else:
    print("MISS: hold")

# 14. Sell
old14 = "<td style=\"color:#ff6b6b\">'+r.sell+'</td>"
new14 = '<td data-label="Sell" style="color:#ff6b6b">'+r.sell+'</td>'
if old14 in segment:
    segment = segment.replace(old14, new14, 1)
    print("OK: sell")
else:
    print("MISS: sell")

# 15. Mkt Cap
old15 = "<td>'+fmtMktcap(r.mktcap)+'</td>"
new15 = '<td data-label="Mkt Cap">'+fmtMktcap(r.mktcap)+'</td>'
if old15 in segment:
    segment = segment.replace(old15, new15, 1)
    print("OK: mkt cap")
else:
    print("MISS: mkt cap")

# 16. Shorts
old16 = "<td style='color:#fff'>'+r.short_int+'%</td>"
new16 = "<td data-label='Shorts' style='color:#fff'>'+r.short_int+'%</td>"
if old16 in segment:
    segment = segment.replace(old16, new16, 1)
    print("OK: shorts")
else:
    print("MISS: shorts")

# 17. IV
old17 = "<td style='color:#fff'>'+r.iv+'%</td>"
new17 = "<td data-label='IV' style='color:#fff'>'+r.iv+'%</td>"
if old17 in segment:
    segment = segment.replace(old17, new17, 1)
    print("OK: iv")
else:
    print("MISS: iv")

# 18. Trend/Squeeze
old18 = "<td>+(r.squeeze?"
new18 = '<td data-label="Trend">+(r.squeeze?'
if old18 in segment:
    segment = segment.replace(old18, new18, 1)
    print("OK: trend")
else:
    print("MISS: trend")

# 19. News
old19 = "<td>'+newsHtml(r.news)+'</td></tr>"
new19 = "<td data-label='News'>'+newsHtml(r.news)+'</td></tr>"
if old19 in segment:
    segment = segment.replace(old19, new19, 1)
    print("OK: news")
else:
    print("MISS: news")

# Check remaining
tds_after = re.findall(r"<td([^>]*)>", segment)
without_after = [t for t in tds_after if 'data-label' not in t]
print(f'\nRemaining TD without data-label: {len(without_after)}')
for t in without_after:
    print(f'  attr: {t[:50]}')

# Write back
content = content[:start] + segment + content[end:]
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('\nWritten!')