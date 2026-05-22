c=open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','r',encoding='utf-8').read()
idx=c.find('.btn{background:#238636')
if idx<0:
    idx=c.find('background:#238636')
print(c[max(0,idx-50):idx+300])