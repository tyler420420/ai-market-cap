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
print('Stock | Score | Days | Sentiment')
print('-' * 55)
for r in rows:
    sent = r.get('sentiment','') or ''
    print(f"  {r['ticker']:6} | {r['score']:3} | {r['days_left']:4}d | {sent or 'N/A'}")
print(f'\nPositive: {sum(1 for r in rows if r.get("sentiment")=="Positive")}')
print(f'Mixed: {sum(1 for r in rows if r.get("sentiment")=="Mixed")}')
print(f'Negative: {sum(1 for r in rows if r.get("sentiment")=="Negative")}')