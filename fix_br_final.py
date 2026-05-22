c=open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','r',encoding='utf-8').read()
# In JSON, \n is a literal backslash-n, not a newline char. JS can't replace it.
# Solution: don't use \n in Python output. Use <br> directly in Python.
# Change Python to output <br> directly, and DON'T replace in JS.
# Fix 1: Change JS to just display r.earnings_date as-is (Python puts <br> in it)
c=c.replace(
    "html+='<td class=earn-cell>'+r.earnings_date+'</td>'",
    "html+='<td class=earn-cell>'+r.earnings_date+'</td>'"
)
# Fix 2: Change Python to put literal <br> instead of \n
c=c.replace(
    "(lambda ed: ed[5:10].replace('-', chr(45)) + chr(10) + ed[:4] if ed else '')(stock.earnings_date)",
    "(lambda ed: '<br>'.join([ed[5:10].replace('-', chr(45)), ed[:4]]) if ed else '')(stock.earnings_date)"
)
open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','w',encoding='utf-8').write(c)
import shutil
shutil.copy('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','C:\\Users\\Tyler_AI\\Desktop\\AI_Market_Cap_Scanner_v2.html')
print('Done')
# Check what's in the data
import re
m = re.search(r'"earnings_date":\s*"[^"]+"', c)
if m: print('Data:', m.group(0))