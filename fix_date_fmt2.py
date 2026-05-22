c=open('ai_earnings_scanner.py','r',encoding='utf-8').read()
old = "function scoreColor(s){return s>=80?'#00ff88':'#58a6ff';}"
new = "function scoreColor(s){return s>=80?'#00ff88':'#58a6ff';}function fmtEdate(s){if(!s)return'';var p=s.split('-');var months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];var m=parseInt(p[0]);return months[m-1]+' '+p[1]+'<br><span style=\"font-size:0.85em;color:#8b949e\">'+p[0]+'</span>';}"
c=c.replace(old,new)
old2 = "html+='<td>'+r.earnings_date+'</td>'"
new2 = "html+='<td style=\"font-size:0.85em\">'+fmtEdate(r.earnings_date)+'</td>'"
c=c.replace(old2,new2)
open('ai_earnings_scanner.py','w',encoding='utf-8').write(c)
print('Done')