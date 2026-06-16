path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_scanner.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# The actual JS uses escaped double quotes inside single-quoted Python strings
old = "html+='<tr style=\"background:'+bg+'\"><td><strong><a href=\"https://finance.yahoo.com/quote/'+r.ticker+'\" target=\"_blank\" style=\"color:#66b2ff\">'+r.ticker+'</a></strong></td>';html+='<td>'+r.company_name.substring(0,35)+(r.company_name.length>35?'...':'')+'</td>';html+='<td><strong style=\"color:'+c+';font-size:1.3em\">'+r.score+'</strong></td>';html+='<td class=earn-cell>'+r.earnings_date.replace(chr(10),'<br>')+'</td>';html+='<td style=\"color:'+(r.days_left==0?'#ff4444':(r.days_left<=7?'#00ff88':'#ffcc00'))+';font-weight:bold\">'+(r.days_left==0?'Today':r.days_left+'d')+'</td>';html+='<td>$'+Math.floor(r.price)+'</td>';html+='<td>$'+Math.floor(r.pe_target)+' | +'+r.pe_upside+'%</td>';html+='<td>$'+Math.floor(r['3d'])+' | +'+r['3d_up']+'%</td>';html+='<td>$'+Math.floor(r['5d'])+' | +'+r['5d_up']+'%</td>';html+='<td>'+r.analysts+'</td>';html+='<td style=\"color:#00ff88\">'+r.sb+'</td>';html+='<td style=\"color:#58a6ff\">'+r.buy+'</td>';html+='<td style=\"color:#ffcc00\">'+r.hold+'</td>';html+='<td style=\"color:#ff6b6b\">'+r.sell+'</td>';html+='<td>'+fmtMktcap(r.mktcap)+'</td>';html+='<td style=\\'color:#fff\\'>'+r.short_int+'%</td>';html+='<td style=\\'color:#fff\\'>'+r.iv+'%</td>';html+='<td>'+(r.squeeze?'<span style=\\'background:#1a2a1a;border:1px solid #2ea043;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#00ff88\\'>Yes</span>':'??')+'</td>';html+='<td>'+newsHtml(r.news)+'</td></tr>';});tbody.innerHTML=html;};sortBy('days_left');"

if old in content:
    print('FOUND')
else:
    print('NOT FOUND')
    # Find the actual content
    idx = content.find("html+='<tr style=\"background:'+bg+'")
    if idx >= 0:
        print('Actual content:')
        print(repr(content[idx:idx+500]))
    else:
        print('Cannot find anchor')