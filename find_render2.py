c=open('ai_earnings_scanner.py','r',encoding='utf-8').read()
idx=c.find("r.company_name.substring")
snippet=c[idx:idx+800]
print(repr(snippet[:600]))