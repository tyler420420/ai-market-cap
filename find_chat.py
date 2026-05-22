c=open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','r',encoding='utf-8').read()
idx=c.find('chat-btn{position')
print(c[idx:idx+200])