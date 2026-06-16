path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find("html+='<tr style")
end = content.find("sortBy('days_left');", start) + len("sortBy('days_left');")
segment = content[start:end]

# Replace using actual characters in the file (not Python-escaped)
# The segment contains literal backslash-quote (\") and backslash-single-quote (\')
replacements = [
    # Ticker - need to find exact pattern in segment
    ("<td><strong><a href", "<td data-label=\"Ticker\"><strong><a href"),
    # Company
    ("<td>'+r.company_name.substring", "<td data-label=\"Company\">'+r.company_name.substring"),
    # Score
    ("<td><strong style=\"color:'+c+';font-size:1.3em\">'+r.score+'</strong></td>",
     "<td data-label=\"Score\"><strong style=\"color:'+c+'\">'+r.score+'</strong></td>"),
    # Earnings
    ("<td class=earn-cell>'+r.earnings_date", "<td data-label=\"Earnings\" class=earn-cell>'+r.earnings_date"),
    # Days
    ("<td style=\"color:'+(r.days_left==0",
     "<td data-label=\"Days\" style=\"color:'+(r.days_left==0"),
    # Analysts
    ("<td>'+r.analysts+'</td>", "<td data-label=\"Analysts\">'+r.analysts+'</td>"),
    # Strong Buy
    ("<td style=\"color:#00ff88\">'+r.sb+'</td>", "<td data-label=\"Strong Buy\" style=\"color:#00ff88\">'+r.sb+'</td>"),
    # Buy
    ("<td style=\"color:#58a6ff\">'+r.buy+'</td>", "<td data-label=\"Buy\" style=\"color:#58a6ff\">'+r.buy+'</td>"),
    # Hold
    ("<td style=\"color:#ffcc00\">'+r.hold+'</td>", "<td data-label=\"Hold\" style=\"color:#ffcc00\">'+r.hold+'</td>"),
    # Sell
    ("<td style=\"color:#ff6b6b\">'+r.sell+'</td>", "<td data-label=\"Sell\" style=\"color:#ff6b6b\">'+r.sell+'</td>"),
    # Mkt Cap
    ("<td>'+fmtMktcap(r.mktcap)+'</td>", "<td data-label=\"Mkt Cap\">'+fmtMktcap(r.mktcap)+'</td>"),
    # Shorts (uses single quotes in HTML)
    ("<td style='color:#fff'>'+r.short_int+'%</td>", "<td data-label='Shorts' style='color:#fff'>'+r.short_int+'%</td>"),
    # IV
    ("<td style='color:#fff'>'+r.iv+'%</td>", "<td data-label='IV' style='color:#fff'>'+r.iv+'%</td>"),
    # Trend
    ("<td>+(r.squeeze?", "<td data-label=\"Trend\">+(r.squeeze?"),
    # News
    ("<td>'+newsHtml(r.news)+'</td></tr>", "<td data-label=\"News\">'+newsHtml(r.news)+'</td></tr>"),
]

changes = 0
for old, new in replacements:
    if old in segment:
        segment = segment.replace(old, new, 1)
        changes += 1
        print(f'OK: {old[:50]}')
    else:
        print(f'MISS: {old[:60]}')

print(f'\nTotal: {changes}/16')
if changes >= 14:
    content = content[:start] + segment + content[end:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Written!')
else:
    print('Not enough - check MISSes above')