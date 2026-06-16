path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_today.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()
idx = content.find('renderTable()')
seg = content[idx:idx+3000]
tidx = seg.find("html+='<tr")
print(repr(seg[tidx:tidx+150]))