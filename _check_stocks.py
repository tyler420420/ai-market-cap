import json, re

with open('C:/Users/Tyler_AI/ai-market-cap/ai_earnings_today.html', 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find('var rowsData=')
arr_depth, json_end = 0, idx
for i in range(idx + 12, len(content)):
    ch = content[i]
    if ch == '[':
        arr_depth += 1
    elif ch == ']':
        arr_depth -= 1
        if arr_depth == 0:
            json_end = i
            break

json_str = content[idx + 13:json_end + 1]
clean = re.sub(r'<br\s*/?>', ' ', json_str)
stocks = json.loads(clean)
print(f'Total stocks: {len(stocks)}')
for s in stocks:
    print(f"  {s['ticker']:6} score={s['score']:3} earnings={s['earnings_date']} days={s['days_left']}")
