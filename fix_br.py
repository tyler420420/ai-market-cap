c=open('ai_earnings_scanner.py','r',encoding='utf-8').read()
old = "function fmtEdate(s){if(!s)return'';var p=s.split('-');var months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];var m=parseInt(p[1]);return months[m-1]+' '+p[2]+'<br><span style=\"font-size:0.85em;color:#8b949e\">'+p[0]+'</span>';}"
new = "function fmtEdate(s){if(!s)return'';var p=s.split('-');var months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];var m=parseInt(p[1]);return months[m-1]+' '+p[2]+' <span style=font-size:0.85em;color:#8b949e>'+p[0]+'</span>';}"
c=c.replace(old,new)
open('ai_earnings_scanner.py','w',encoding='utf-8').write(c)
print('Done')