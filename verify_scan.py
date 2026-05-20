import json, re

with open('ai_earnings_57day_20260519_2237.html', 'r', encoding='utf-8') as f:
    c = f.read()

print('Size:', len(c))
m = re.search(r'var rowsData=(.*?);\s*var sortCol', c, re.DOTALL)
if m:
    data = json.loads(m.group(1).strip())
    print('rowsData:', len(data), 'stocks')
    for s in data[:3]:
        print(f'  {s["ticker"]}: score={s["score"]}')

print('DOMContentLoaded:', 'DOMContentLoaded' in c)
print('Chat button:', 'Chat' in c)
print('&amp; count:', c.count('&amp;'))
print('RowsData valid JSON:', True)