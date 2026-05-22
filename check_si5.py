import json

with open('ai_earnings_today.html','r', encoding='utf-8') as f:
    html = f.read()

# Find the script that starts with rowsData
idx = html.find('<script>var rowsData=')
if idx == -1:
    idx = html.find('var rowsData=')

script = html[idx:]
print(f'Script starts: {script[:50]}')

# Find the end of THIS script block only
first_script_end = script.find('</script>')
print(f'First </script> at: {first_script_end}')

json_text = script[12:first_script_end]
print(f'JSON text length: {len(json_text)}')

if json_text.startswith('='):
    json_text = json_text[1:]

try:
    rows = json.loads(json_text)
    print(f'Parsed {len(rows)} rows\n')
    print(f'Stock | Short Int | Score | Days | Squeeze')
    print('-' * 60)
    for r in rows:
        si = r.get('short_int', 0) or 0
        score = r.get('score', 0)
        days = r.get('days_left', 0)
        sqz = '🔥' if si > 10 and days <= 10 else ''
        si_str = f"{si}%" if si > 0 else "N/A"
        print(f"  {r['ticker']:6} | {si_str:10} | {score:3} | {days:4}d | {sqz}")
except json.JSONDecodeError as e:
    print(f'Error: {e}')