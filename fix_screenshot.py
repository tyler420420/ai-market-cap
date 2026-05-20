with open('index.html','r',encoding='utf-8',errors='replace') as f: c=f.read()
c = c.replace('src="screenshot.png"', 'src="https://agent-cdn.minimax.io/mcp/anon/general/1779161144_7cf419da.png"')
open('index.html','w',encoding='utf-8',newline='').write(c)
print('Updated screenshot URL')
