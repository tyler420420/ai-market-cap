c=open('ai_earnings_scanner.py','r',encoding='utf-8').read()
old = "#chat-btn:hover{background:#2ea043}"
new = "#chat-btn:hover{background:#2ea043}"
# The hover on gold doesn't look right - let's keep it same gold on hover but maybe a slightly darker gold
# Actually the gold on hover to green is fine since run scan button also goes green. 
# But let's make chat button hover stay gold - just slightly darker
c=c.replace(old, "#chat-btn:hover{background:#e6c200}")
open('ai_earnings_scanner.py','w',encoding='utf-8').write(c)
print('Done')