path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the JS row section: from "html+='<tr style" to "sortBy('days_left');"
start = content.find("html+=\'<tr style")
end = content.find("sortBy('days_left');", start) + len("sortBy('days_left');")
if start < 0:
    print('Start not found')
else:
    segment = content[start:end]
    print(f'Segment length: {len(segment)}')
    
    # Now do targeted replacements - replace each '<td>' opening with '<td data-label="X">'
    # We need to know which column each <td> corresponds to
    # The order in the segment is:
    # 1. Ticker
    # 2. Company name
    # 3. Score
    # 4. Earnings date
    # 5. Days left
    # 6. Price
    # 7. PE target (3 Day)
    # 8. 3d (7 Day)
    # 9. 5d (14 Day)
    # 10. Analysts
    # 11. SB
    # 12. Buy
    # 13. Hold
    # 14. Sell
    # 15. Mkt cap
    # 16. Shorts
    # 17. IV
    # 18. Trend/Sentiment
    # 19. News
    
    labels = ['Ticker', 'Company', 'Score', 'Earnings', 'Days', 'Price',
              '3 Day', '7 Day', '14 Day', 'Analysts', 'Strong Buy', 'Buy',
              'Hold', 'Sell', 'Mkt Cap', 'Shorts', 'IV', 'Trend', 'News']
    
    new_segment = segment
    for i, label in enumerate(labels):
        # Replace the Nth occurrence of '</td>';html+=... or just count <td> occurrences
        # Actually, let's just do sequential replacements
        pass
    
    # Simpler: do sequential replacements of the specific patterns
    # Each <td> pattern is unique enough
    replacements = [
        ("html+=\'<td><strong><a href=\\\"https://finance.yahoo.com/quote/\'+r.ticker+\'\\\" target=\\\"_blank\\\" style=\\\"color:#66b2ff\\\">\'+r.ticker+\'</a></strong></td>\';",
         "html+=\'<td data-label=\\\"Ticker\\\"><strong><a href=\\\"https://finance.yahoo.com/quote/\'+r.ticker+\'\\\" target=\\\"_blank\\\" style=\\\"color:#66b2ff\\\">\'+r.ticker+\'</a></strong></td>\';"),
        ("html+=\'<td>\'+r.company_name.substring(0,35)+(r.company_name.length>35?\'...\':\'\')+\'</td>\';",
         "html+=\'<td data-label=\\\"Company\\\">\'+r.company_name.substring(0,35)+(r.company_name.length>35?\'...\':\'\')+\'</td>\';"),
        ("html+=\'<td><strong style=\\\"color:\'+c+\';font-size:1.3em\\\">\'+r.score+\'</strong></td>\';",
         "html+=\'<td data-label=\\\"Score\\\"><strong style=\\\"color:\'+c+\'\\\">\'+r.score+\'</strong></td>\';"),
        ("html+=\'<td class=earn-cell>\'+r.earnings_date.replace(chr(10),\'<br>\')+\'</td>\';",
         "html+=\'<td data-label=\\\"Earnings\\\" class=earn-cell>\'+r.earnings_date.replace(chr(10),\'<br>\')+\'</td>\';"),
        ("html+=\'<td style=\\\"color:\'+(r.days_left==0?\'#ff4444\':(r.days_left<=7?\'#00ff88\':\'#ffcc00\'))+\';font-weight:bold\\\">\'+(r.days_left==0?\'Today\':r.days_left+\'d\')+\'</td>\';",
         "html+=\'<td data-label=\\\"Days\\\" style=\\\"color:\'+(r.days_left==0?\'#ff4444\':(r.days_left<=7?\'#00ff88\':\'#ffcc00\'))+\';font-weight:bold\\\">\'+(r.days_left==0?\'Today\':r.days_left+\'d\')+\'</td>\';"),
        ("html+=\'<td>$'+Math.floor(r.price)+'</td>\';",
         "html+=\'<td data-label=\\\"Price\\\">$'+Math.floor(r.price)+'</td>\';"),
        ("html+=\'<td><strong>$'+Math.floor(r.pe_target)+'</strong> <span style=\\\"color:#00ff88\\\">+\'+r.pe_upside+\'%</span></td>\';",
         "html+=\'<td data-label=\\\"3 Day\\\"><strong>$'+Math.floor(r.pe_target)+'</strong> <span style=\\\"color:#00ff88\\\">+\'+r.pe_upside+\'%</span></td>\';"),
        ("html+=\'<td>$'+Math.floor(r['3d'])+' <span style=\\\"color:#00ff88\\\">+\'+r['3d_up']+\'%</span></td>\';",
         "html+=\'<td data-label=\\\"7 Day\\\">$'+Math.floor(r['3d'])+' <span style=\\\"color:#00ff88\\\">+\'+r['3d_up']+\'%</span></td>\';"),
        ("html+=\'<td>$'+Math.floor(r['5d'])+' <span style=\\\"color:#00ff88\\\">+\'+r['5d_up']+\'%</span></td>\';",
         "html+=\'<td data-label=\\\"14 Day\\\">$'+Math.floor(r['5d'])+' <span style=\\\"color:#00ff88\\\">+\'+r['5d_up']+\'%</span></td>\';"),
        ("html+=\'<td>\'+r.analysts+\'</td>\';",
         "html+=\'<td data-label=\\\"Analysts\\\">\'+r.analysts+\'</td>\';"),
        ("html+=\'<td style=\\\"color:#00ff88\\\">\'+r.sb+\'</td>\';",
         "html+=\'<td data-label=\\\"Strong Buy\\\" style=\\\"color:#00ff88\\\">\'+r.sb+\'</td>\';"),
        ("html+=\'<td style=\\\"color:#58a6ff\\\">\'+r.buy+\'</td>\';",
         "html+=\'<td data-label=\\\"Buy\\\" style=\\\"color:#58a6ff\\\">\'+r.buy+\'</td>\';"),
        ("html+=\'<td style=\\\"color:#ffcc00\\\">\'+r.hold+\'</td>\';",
         "html+=\'<td data-label=\\\"Hold\\\" style=\\\"color:#ffcc00\\\">\'+r.hold+\'</td>\';"),
        ("html+=\'<td style=\\\"color:#ff6b6b\\\">\'+r.sell+\'</td>\';",
         "html+=\'<td data-label=\\\"Sell\\\" style=\\\"color:#ff6b6b\\\">\'+r.sell+\'</td>\';"),
        ("html+=\'<td>\'+fmtMktcap(r.mktcap)+\'</td>\';",
         "html+=\'<td data-label=\\\"Mkt Cap\\\">\'+fmtMktcap(r.mktcap)+\'</td>\';"),
        ("html+=\"<td style='color:#fff'>\"+r.short_int+'%</td>\';",
         "html+=\"<td data-label='Shorts' style='color:#fff'>\"+r.short_int+'%</td>\';"),
        ("html+=\"<td style='color:#fff'>\"+r.iv+'%</td>\';",
         "html+=\"<td data-label='IV' style='color:#fff'>\"+r.iv+'%</td>\';"),
        ("html+=\'<td>\'+(r.sentiment==\'Positive\'?\'<span style=\\\"background:#1a2a1a;border:1px solid #2ea043;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#00ff88\\\">\'+r.sentiment+\'</span>\':r.sentiment==\'Mixed\'?\'<span style=\\\"background:#2a2a1a;border:1px solid #ffd700;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#ffd700\\\">\'+r.sentiment+\'</span>\':\'<span style=\\\"background:#2a1a1a;border:1px solid #ff4444;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#ff6b6b\\\">\'+r.sentiment+\'</span>\')+\'</td>\';",
         "html+=\'<td data-label=\\\"Trend\\\">\'+(r.sentiment==\'Positive\'?\'<span style=\\\"background:#1a2a1a;border:1px solid #2ea043;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#00ff88\\\">\'+r.sentiment+\'</span>\':r.sentiment==\'Mixed\'?\'<span style=\\\"background:#2a2a1a;border:1px solid #ffd700;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#ffd700\\\">\'+r.sentiment+\'</span>\':\'<span style=\\\"background:#2a1a1a;border:1px solid #ff4444;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#ff6b6b\\\">\'+r.sentiment+\'</span>\')+\'</td>\';"),
        ("html+=\'<td>\'+newsHtml(r.news)+\'</td></tr>\';",
         "html+=\'<td data-label=\\\"News\\\">\'+newsHtml(r.news)+\'</td></tr>\';"),
    ]
    
    # Do replacements
    changes = 0
    for old, new in replacements:
        if old in segment:
            segment = segment.replace(old, new, 1)
            changes += 1
            print(f'Replaced pattern {changes}')
        else:
            print(f'NOT FOUND: {old[:60]}...')
    
    if changes > 0:
        content = content[:start] + segment + content[end:]
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Done - {changes} replacements')
    else:
        print('No replacements made')