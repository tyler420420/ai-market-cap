c=open('ai_earnings_scanner.py','r',encoding='utf-8').read()
idx=c.find("r.earnings_date+'<td>'")
print(repr(c[idx-50:idx+100]))