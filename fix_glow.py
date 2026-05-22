c=open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','r',encoding='utf-8').read()
# Add glow to Run Scan button
old = '.btn:active{background:#238636}'
new = '.btn:active{background:#238636}.btn{box-shadow:0 0 12px rgba(255,215,0,0.5)}'
c=c.replace(old,new)
# Add glow to Refresh button
old2 = '#refreshBtn:hover{background:#388bfd}'
new2 = '#refreshBtn{box-shadow:0 0 12px rgba(31,111,235,0.5)}#refreshBtn:hover{background:#388bfd}'
c=c.replace(old2,new2)
# Add glow to Chat button
old3 = 'chat-btn{position:fixed;bottom:24px;right:24px;background:#ffd700;color:#000;border:none;border-radius:10px;padding:14px 28px;font-size:1.05em;font-weight:bold;cursor:pointer;box-shadow:0 4px 20px rgba'
new3 = 'chat-btn{position:fixed;bottom:24px;right:24px;background:#ffd700;color:#000;border:none;border-radius:10px;padding:14px 28px;font-size:1.05em;font-weight:bold;cursor:pointer;box-shadow:0 0 12px rgba(255,215,0,0.5)}'
c=c.replace(old3,new3)
open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','w',encoding='utf-8').write(c)
import shutil
shutil.copy('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','C:\\Users\\Tyler_AI\\Desktop\\AI_Market_Cap_Scanner_v2.html')
print('Done')