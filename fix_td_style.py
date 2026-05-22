c=open('ai_earnings_scanner.py','r',encoding='utf-8').read()
# The issue: style="font-size:0.85em;white-space:pre-line" has a semicolon inside a double-quoted
# Python string - the semicolon terminates the string. Fix by removing white-space:pre-line
old = "html+='<td style=\"font-size:0.85em;white-space:pre-line\">'+fmtEdate"
new = "html+='<td style=\"font-size:0.85em\">'+fmtEdate"
c=c.replace(old,new)
open('ai_earnings_scanner.py','w',encoding='utf-8').write(c)
print('Done')