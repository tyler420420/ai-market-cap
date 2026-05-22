c=open('ai_earnings_scanner.py','r',encoding='utf-8').read()
idx=c.find("earnings_date")
print(c[idx:idx+100])