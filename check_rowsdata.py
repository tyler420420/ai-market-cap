import re, json

with open('C:/Users/Tyler_AI/Desktop/14 days earning screener.html', 'r', encoding='utf-8') as f:
    c = f.read()

m = re.search(r'var rowsData=(.*?);\s*var sortCol', c, re.DOTALL)
if m:
    raw = m.group(1).strip()
    print(f'rowsData length: {len(raw)} chars')
    try:
        data = json.loads(raw)
        print(f'Valid JSON! {len(data)} stocks')
        for s in data[:5]:
            print(f'  {s["ticker"]}: score={s["score"]}, days={s["days_left"]}')
    except Exception as e:
        print(f'JSON ERROR: {e}')
        # Find error position
        err_str = str(e)
        if 'char' in err_str:
            pos = int(err_str.split('char ')[-1].rstrip(')').split(' ')[-1])
            print(f'Error near position {pos}')
            print(f'Context: {repr(raw[max(0,pos-100):pos+100])}')
else:
    print('rowsData not found')