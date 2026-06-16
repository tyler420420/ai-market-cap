path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Read the actual segment from temp file to get exact patterns
with open(r'C:\Users\Tyler_AI\ai-market-cap\temp_segment.txt', 'r', encoding='utf-8') as f:
    segment = f.read().split('\n')[0]  # first line only

print(f'Segment length: {len(segment)}')

# Now do remaining replacements using the EXACT patterns from the file
replacements = [
    ("<td>$'+Math.floor(r.price)+'</td>",
     "<td data-label=\"Price\">$'+Math.floor(r.price)+'</td>"),
    ("<td>$'+Math.floor(r.pe_target)+' | +'+r.pe_upside+'%</td>",
     "<td data-label=\"3 Day\"><strong>$'+Math.floor(r.pe_target)+'</strong> <span style=\"color:#00ff88\">+'+r.pe_upside+'%</span></td>"),
    ("<td>$'+Math.floor(r['3d'])+' | +'+r['3d_up']+'%</td>",
     "<td data-label=\"7 Day\">$'+Math.floor(r['3d'])+' <span style=\"color:#00ff88\">+'+r['3d_up']+'%</span></td>"),
    ("<td>$'+Math.floor(r['5d'])+' | +'+r['5d_up']+'%</td>",
     "<td data-label=\"14 Day\">$'+Math.floor(r['5d'])+' <span style=\"color:#00ff88\">+'+r['5d_up']+'%</span></td>"),
    ("<td style='color:#fff'>'+r.short_int+'%</td>",
     "<td data-label='Shorts' style='color:#fff'>'+r.short_int+'%</td>"),
    ("<td style='color:#fff'>'+r.iv+'%</td>",
     "<td data-label='IV' style='color:#fff'>'+r.iv+'%</td>"),
    ("<td>+(r.squeeze?'<span style='background:#1a2a1a;border:1px solid #2ea043;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#00ff88'>Yes</span>':'â€\"')+'</td>",
     "<td data-label=\"Trend\">'+(r.squeeze?'<span style=\"background:#1a2a1a;border:1px solid #2ea043;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#00ff88\">Yes</span>':r.sentiment=='Positive'?'<span style=\"background:#1a2a1a;border:1px solid #2ea043;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#00ff88\">'+r.sentiment+'</span>':r.sentiment=='Mixed'?'<span style=\"background:#2a2a1a;border:1px solid #ffd700;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#ffd700\">'+r.sentiment+'</span>':'<span style=\"background:#2a1a1a;border:1px solid #ff4444;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#ff6b6b\">'+r.sentiment+'</span>')+'</td>"),
    ("<td>'+newsHtml(r.news)+'</td></tr>",
     "<td data-label=\"News\">'+newsHtml(r.news)+'</td></tr>"),
]

changes = 0
for old, new in replacements:
    if old in segment:
        segment = segment.replace(old, new, 1)
        changes += 1
        print(f'Replaced: {old[:50]}...')
    else:
        print(f'NOT FOUND: {old[:60]}...')

print(f'Total changes: {changes}')

if changes > 0:
    # Replace in the full content
    start = content.find("html+='<tr style")
    end = content.find("sortBy('days_left');", start) + len("sortBy('days_left');")
    content = content[:start] + segment + content[end:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Written')
else:
    print('No changes')