f=open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','r',encoding='utf-8')
c=f.read()
f.close()
old = 'Upgrade to Run Scan + Chat'
new = '<a href="/pricing" style="color:#ffd700;text-decoration:underline">Upgrade to Run Scan + Chat</a>'
c=c.replace(old,new)
f=open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','w',encoding='utf-8')
f.write(c)
f.close()
print('done')