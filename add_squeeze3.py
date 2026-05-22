import re

with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Add squeeze cell to renderTable - after r.iv and before newsHtml
old = "html+='<td style=\"color:#fff\">'+r.iv+'%</td>';html+='<td>'+newsHtml(r.news)+'</td></tr>';"
new = "html+='<td style=\"color:#fff\">'+r.iv+'%</td>';html+='<td>'+(r.squeeze?'<span style=\"background:#1a0a0a;border:1px solid #ff4444;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#ff6b6b\">SQUEEZE</span>':'—')+'</td>';html+='<td>'+newsHtml(r.news)+'</td></tr>';"
if old in c:
    c = c.replace(old, new)
    print('Done: squeeze cell added to renderTable')
else:
    print('FAILED: pattern not found')

with open('ai_earnings_scanner.py', 'w', encoding='utf-8') as f:
    f.write(c)