c=open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','r',encoding='utf-8').read()
# The earn-cell replace is stripping the br. Fix to NOT replace in JS since Python already put <br>
c=c.replace(
    "html+='<td class=earn-cell>'+r.earnings_date.replace(chr(10),'<br>')+'</td>'",
    "html+='<td class=earn-cell>'+r.earnings_date+'</td>'"
)
open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','w',encoding='utf-8').write(c)
import shutil
shutil.copy('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','C:\\Users\\Tyler_AI\\Desktop\\AI_Market_Cap_Scanner_v2.html')
print('Done')