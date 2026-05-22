c=open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','r',encoding='utf-8').read()
idx=c.find('pick-banner')
print(c[idx:idx+200])