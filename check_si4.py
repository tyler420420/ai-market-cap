import json

with open('ai_earnings_today.html','r', encoding='utf-8') as f:
    html = f.read()

idx = html.find('var rowsData=')
script = html[idx:]
end_marker = script.find('</script>')
json_text = script[12:end_marker]  # skip "var rowsData="

# Fix: the string starts with "=" so skip the "="
if json_text.startswith('='):
    json_text = json_text[1:]

rows = json.loads(json_text)
print(f'Stock | Short Int | Score | Days | Squeeze')
print('-' * 60)
for r in rows:
    si = r.get('short_int', 0) or 0
    score = r.get('score', 0)
    days = r.get('days_left', 0)
    sqz = '🔥 SQZ' if si > 10 and days <= 10 else ''
    si_str = f"{si}%" if si > 0 else "N/A"
    print(f"  {r['ticker']:6} | {si_str:10} | {score:3} | {days:4}d | {sqz}")