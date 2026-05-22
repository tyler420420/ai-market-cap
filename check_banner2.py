c=open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','r',encoding='utf-8').read()
import re
# Check if pick-banner has inline style override
m = re.search(r'class=pick-banner[^>]*style=([^>\s]+)', c)
if m: print('INLINE:', repr(m.group(0)))
# Check for background on the element itself
m2 = re.search(r'<div class=pick-banner[^>]*>', c)
if m2: print('ELEMENT:', repr(m2.group(0)))