f=open('ai_earnings_today.html','r',encoding='utf-8')
c=f.read()
f.close()
# Fix earnings days yellow to green
c=c.replace('color:#ffcc00">1 days','color:#00ff88">1 days')
c=c.replace('color:#ffcc00">8 days','color:#00ff88">8 days')
# Fix sell price blue to green in banner - check for exact pattern
if 'color:#58a6ff">' in c:
    c=c.replace('color:#58a6ff">','color:#00ff88">')
f=open('ai_earnings_today.html','w',encoding='utf-8')
f.write(c)
f.close()
print('done')