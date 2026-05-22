c=open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','r',encoding='utf-8').read()
old = 'href="/pricing" style="color:#ffd700;text-decoration:underline"'
new = 'href="/pricing" style="color:#ffd700;text-decoration:underline" onmouseover="this.style.color=\'#2ea043\'" onmouseout="this.style.color=\'#ffd700\'"'
c=c.replace(old,new)
open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','w',encoding='utf-8').write(c)
import shutil
shutil.copy('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','C:\\Users\\Tyler_AI\\Desktop\\AI_Market_Cap_Scanner_v2.html')
print('Done')