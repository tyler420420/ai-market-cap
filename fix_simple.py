c=open('ai_earnings_scanner.py','r',encoding='utf-8').read()
# Replace the earnings_date in rowsData to strip year, format nicely
old = "'earnings_date': stock.earnings_date.replace('2026-','').replace('2025-',''),"
new = "'earnings_date': stock.earnings_date,"
c=c.replace(old,new)

# Add a simpler fmtEdate that works - just format without newline
old2 = "function fmtEdate(s){if(!s)return'';var p=s.split('-');var months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];var m=parseInt(p[1]);return months[m-1]+' '+p[2]+'\\n'+p[0];}"
new2 = "function fmtEdate(s){if(!s)return'';var p=s.split('-');var months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];var m=parseInt(p[1]);return months[m-1]+' '+p[2]+'/'+p[0];}"
c=c.replace(old2,new2)

# Also use white-space:pre-line on the earnings date cell so newlines display properly
old3 = "html+='<td style=\"font-size:0.85em\">'+fmtEdate(r.earnings_date)+'</td>'"
new3 = "html+='<td style=\"font-size:0.85em;white-space:pre-line\">'+fmtEdate(r.earnings_date)+'</td>'"
c=c.replace(old3,new3)

open('ai_earnings_scanner.py','w',encoding='utf-8').write(c)
print('Done')