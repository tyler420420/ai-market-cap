f=open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','r',encoding='utf-8')
c=f.read()
f.close()
c=c.replace("'3d'","'3 Day'")
c=c.replace("'5d'","'5 Day'")
c=c.replace('>3d<','>3 Day<')
c=c.replace('>5d<','>5 Day<')
c=c.replace('Great Earnings Report','Great Earnings Report')
c=c.replace('Excellent Earnings Report','Excellent Earnings Report')
open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','w',encoding='utf-8').write(c)
import shutil
shutil.copy('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','C:\\Users\\Tyler_AI\\Desktop\\AI_Market_Cap_Scanner_v2.html')
print('Done')
import re
for lbl in ['3 Day','5 Day']:
    print(lbl, 'in page:', lbl in c)