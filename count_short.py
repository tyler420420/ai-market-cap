import json
with open('ai_earnings_today.html','r',encoding='utf-8') as f: h=f.read()
i=h.find('<script>var rowsData=')
ds=h[i+17:h.find('</script>',i)]
d=0;ie=False;e=False;ae=0
for j,ch in enumerate(ds):
    if e: e=False; continue
    if ch=='\\': e=True; continue
    if ch=='"' and not e: ie=not ie; continue
    if ie: continue
    if ch=='{': d+=1
    elif ch=='}': d-=1
    elif ch=='[': d+=1
    elif ch==']': d-=1; ae=j+1
    if d==0 and ae>0: break
rows=json.loads(ds[:ae])
shorts=[r for r in rows if r.get('squeeze')]
print(f'SHORT candidates: {len(shorts)}')
for r in shorts:
    print(f"  {r['ticker']}: {r['short_int']}% SI, {r['days_left']}d, score={r['score']}")
print(f'\nSHORT in HTML: {h.count("SHORT")}')