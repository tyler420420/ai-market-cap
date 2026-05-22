import json, re

with open('ai_earnings_today.html','r', encoding='utf-8') as f:
    html = f.read()

# Extract rowsData using Python slice on the raw string
idx = html.find('var rowsData=')
script = html[idx:]

# Replace </script> with a marker to find end
end_marker = script.find('</script>')
if end_marker == -1:
    print('No </script> found')
    exit(1)

json_text = script[12:end_marker]  # skip "var rowsData="
print(f'JSON text length: {len(json_text)}')
print(f'First 300 chars: {json_text[:300]}')

# Try to parse
try:
    rows = json.loads(json_text)
    print(f'Parsed {len(rows)} rows')
    for r in rows:
        si = r.get('short_int', 0) or 0
        score = r.get('score', 0)
        days = r.get('days_left', 0)
        sqz = '🔥' if si > 10 and days <= 10 else ''
        si_str = f"{si}%" if si > 0 else "N/A"
        print(f"  {r['ticker']:6} | SI={si_str:10} | Score={score:3} | {days}d | {sqz}")
except json.JSONDecodeError as e:
    print(f'JSON parse error: {e}')
    print(f'At position: {e.pos} around: {json_text[e.pos-20:e.pos+20]}')