import json, re
from pathlib import Path

desktop_test = Path(r'C:\Users\Tyler_AI\Desktop\test_scanner.html')
today_path = Path('ai_earnings_today.html')

if not desktop_test.exists():
    print('ERROR: test_scanner.html not found on Desktop')
    exit(1)

print('Patching test_scanner.html with fresh data...')

# Read fresh rowsData from ai_earnings_today.html
fresh_content = today_path.read_text(encoding='utf-8')
fresh_idx = fresh_content.find('var rowsData=')
arr_depth, fresh_end = 0, fresh_idx
for i in range(fresh_idx + 13, len(fresh_content)):
    ch = fresh_content[i]
    if ch == '[': arr_depth += 1
    elif ch == ']':
        arr_depth -= 1
        if arr_depth == 0:
            fresh_end = i
            break
fresh_rows = fresh_content[fresh_idx + 13: fresh_end + 1]
print(f'Fresh rowsData: {len(fresh_rows)} bytes')

# Read and patch test_scanner.html
test_content = desktop_test.read_text(encoding='utf-8')
scan_idx = test_content.find('var rowsData=')
arr_depth, scan_end = 0, scan_idx
for i in range(scan_idx + 13, len(test_content)):
    ch = test_content[i]
    if ch == '[': arr_depth += 1
    elif ch == ']':
        arr_depth -= 1
        if arr_depth == 0:
            scan_end = i
            break
print(f'test_scanner.html: rowsData at {scan_idx}-{scan_end}')

new_test = test_content[:scan_idx + 13] + fresh_rows + ';'

# Patch counters
rows = json.loads(fresh_rows)
strong_count = sum(1 for r in rows if r.get('score', 0) >= 75)
watch_count = sum(1 for r in rows if 70 <= r.get('score', 0) < 75)

sb_pat = r'(<span style="font-weight:bold;color:#2ea043">)\d+(</span> <span style="color:#8b949e">Strong Buy</span>)'
new_test = re.sub(sb_pat, r'\g<1>' + str(strong_count) + r'\g<2>', new_test, count=1)
wa_pat = r'(<span style="font-weight:bold;color:#58a6ff">)\d+(</span> <span style="color:#8b949e">Watch</span>)'
new_test = re.sub(wa_pat, r'\g<1>' + str(watch_count) + r'\g<2>', new_test, count=1)

desktop_test.write_text(new_test, encoding='utf-8')
print(f'DONE: test_scanner.html updated ({len(new_test)} bytes)')
print(f'Counters: {strong_count} SB, {watch_count} Watch')

# Show first 3 stocks
for s in rows[:3]:
    print(f'  {s["ticker"]}: ${s["price"]}, {s["days_left"]}d')
