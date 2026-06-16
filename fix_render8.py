path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Read the actual line 794
lines = content.split('\n')
line = lines[793]  # 0-indexed
print(f"Line 794 length: {len(line)}")

# The cell rendering part starts after "html+='<tr style\"background:'+bg+'\""
start_marker = "html+='<tr style"
idx = line.find(start_marker)
print(f"Start marker at: {idx}")

# Find where sortBy('days_left') ends the block
end_marker = "sortBy('days_left');"
end_idx = line.find(end_marker, idx)
print(f"End marker at: {end_idx}")

old_block = line[idx:end_idx + len(end_marker)]
print(f"Old block length: {len(old_block)}")
print(f"Old block (repr): {repr(old_block[:100])}")

# Build the new block with data-label
new_block = old_block

# Replace each cell: '<td>' becomes '<td data-label="Label">'
import re

# Simple replacements for each cell
replacements = [
    ("'<tr style\"background:'+bg+'\"'><td><strong><a href=\"https://finance.yahoo.com/quote/'+r.ticker+'\" target=\"_blank\" style=\"color:#66b2ff\">'+r.ticker+'</a></strong></td>';html+='<td>'+r.company_name.substring(0,35)+(r.company_name.length>35?'...':'')+'</td>';html+='<td><strong style=\"color:'+c+';font-size:1.3em\">'+r.score+'</strong></td>';html+='<td class=earn-cell>'+r.earnings_date.replace(chr(10),'<br>')+'</td>';html+='<td style=\"color:'+(r.days_left==0?'#ff4444':(r.days_left<=7?'#00ff88':'#ffcc00'))+';font-weight:bold\">'+(r.days_left==0?'Today':r.days_left+'d')+'</td>';html+='<td>$'+Math.floor(r.price)+'</td>';html+='<td>$'+Math.floor(r.pe_target)+' | +'+r.pe_upside+'%</td>';html+='<td>$'+Math.floor(r['3d'])+' | +'+r['3d_up']+'%</td>';html+='<td>$'+Math.floor(r['5d'])+' | +'+r['5d_up']+'%</td>';html+='<td>'+r.analysts+'</td>';html+='<td style=\"color:#00ff88\">'+r.sb+'</td>';html+='<td style=\"color:#58a6ff\">'+r.buy+'</td>';html+='<td style=\"color:#ffcc00\">'+r.hold+'</td>';html+='<td style=\"color:#ff6b6b\">'+r.sell+'</td>';html+='<td>'+fmtMktcap(r.mktcap)+'</td>';html+=\"<td style='color:#fff'>\"+r.short_int+'%</td>';html+=\"<td style='color:#fff'>\"+r.iv+'%</td>';html+='<td>'+(r.squeeze?'<span style=\\'background:#1a2a1a;border:1px solid #2ea043;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#00ff88\\'>Yes</span>':'??')+'</td>';html+='<td>'+newsHtml(r.news)+'</td>",
     "'<tr style\"background:'+bg+'\"'><td data-label=\"Ticker\"><strong><a href=\"https://finance.yahoo.com/quote/'+r.ticker+'\" target=\"_blank\" style=\"color:#66b2ff\">'+r.ticker+'</a></strong></td>';html+='<td data-label=\"Company\">'+r.company_name.substring(0,35)+(r.company_name.length>35?'...':'')+'</td>';html+='<td data-label=\"Score\"><strong style=\"color:'+c+'\">'+r.score+'</strong></td>';html+='<td data-label=\"Earnings\" class=earn-cell>'+r.earnings_date.replace(chr(10),'<br>')+'</td>';html+='<td data-label=\"Days\" style=\"color:'+(r.days_left==0?'#ff4444':(r.days_left<=7?'#00ff88':'#ffcc00'))+';font-weight:bold\">'+(r.days_left==0?'Today':r.days_left+'d')+'</td>';html+='<td data-label=\"Price\">$'+Math.floor(r.price)+'</td>';html+='<td data-label=\"3 Day\"><strong>$'+Math.floor(r.pe_target)+'</strong> <span style=\"color:#00ff88\">+'+r.pe_upside+'%</span></td>';html+='<td data-label=\"7 Day\">$'+Math.floor(r['3d'])+' <span style=\"color:#00ff88\">+'+r['3d_up']+'%</span></td>';html+='<td data-label=\"14 Day\">$'+Math.floor(r['5d'])+' <span style=\"color:#00ff88\">+'+r['5d_up']+'%</span></td>';html+='<td data-label=\"Analysts\" style=\"color:#bf8fff\">'+r.analysts+'</td>';html+='<td data-label=\"Strong Buy\" style=\"color:#00ff88\">'+r.sb+'</td>';html+='<td data-label=\"Buy\" style=\"color:#58a6ff\">'+r.buy+'</td>';html+='<td data-label=\"Hold\" style=\"color:#ffcc00\">'+r.hold+'</td>';html+='<td data-label=\"Sell\" style=\"color:#ff6b6b\">'+r.sell+'</td>';html+='<td data-label=\"Mkt Cap\">'+fmtMktcap(r.mktcap)+'</td>';html+=\"<td data-label='Shorts' style='color:#fff'>\"+r.short_int+'%</td>';html+=\"<td data-label='IV' style='color:#fff'>\"+r.iv+'%</td>';html+='<td data-label=\"Trend\">'+(r.sentiment=='Positive'?'<span style=\"background:#1a2a1a;border:1px solid #2ea043;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#00ff88\">'+r.sentiment+'</span>':r.sentiment=='Mixed'?'<span style=\"background:#2a2a1a;border:1px solid #ffd700;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#ffd700\">'+r.sentiment+'</span>':'<span style=\"background:#2a1a1a;border:1px solid #ff4444;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#ff6b6b\">'+r.sentiment+'</span>')+'</td>';html+='<td data-label=\"News\">'+newsHtml(r.news)+'</td>")
]

if old_block in content:
    print('Found in content')
else:
    print('NOT FOUND in content')
    # Check if the block is in line 794
    if old_block in line:
        print('Found in line 794')
    else:
        print('Not in line 794 either')
        # Try to find it by searching for part of it
        partial = old_block[:100]
        if partial in content:
            print('Partial found')
        else:
            print('Partial not found')