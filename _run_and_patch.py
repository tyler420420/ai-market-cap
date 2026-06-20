import subprocess, sys, json, re
from pathlib import Path

print('Running scanner locally...')
result = subprocess.run(
    [sys.executable, 'ai_earnings_scanner.py'],
    capture_output=True, text=True, encoding='utf-8', errors='replace',
    timeout=150
)
print('Scanner done.')
if result.stderr:
    # Show just non-404 errors
    lines = [l for l in result.stderr.split('\n') if '404' not in l and l.strip()]
    if lines: print('Stderr:', '\n'.join(lines[:5]))
else:
    print('No stderr')

today_path = Path('ai_earnings_today.html')
scanner_path = Path('scanner.html')
original_scanner = scanner_path.read_text(encoding='utf-8')

try:
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

    scanner_content = scanner_path.read_text(encoding='utf-8')
    scan_idx = scanner_content.find('var rowsData=')
    arr_depth, scan_end = 0, scan_idx
    for i in range(scan_idx + 13, len(scanner_content)):
        ch = scanner_content[i]
        if ch == '[': arr_depth += 1
        elif ch == ']':
            arr_depth -= 1
            if arr_depth == 0:
                scan_end = i
                break
    new_scanner = scanner_content[:scan_idx + 13] + fresh_rows + ';'

    rows = json.loads(fresh_rows)
    strong_count = sum(1 for r in rows if r.get('score', 0) >= 75)
    watch_count = sum(1 for r in rows if 70 <= r.get('score', 0) < 75)

    # Strong Buy counter
    sb_pat = r'(<span style="font-weight:bold;color:#2ea043">)\d+(</span> <span style="color:#8b949e">Strong Buy</span>)'
    new_scanner = re.sub(sb_pat, r'\g<1>' + str(strong_count) + r'\g<2>', new_scanner, count=1)
    # Watch counter
    wa_pat = r'(<span style="font-weight:bold;color:#58a6ff">)\d+(</span> <span style="color:#8b949e">Watch</span>)'
    new_scanner = re.sub(wa_pat, r'\g<1>' + str(watch_count) + r'\g<2>', new_scanner, count=1)

    scanner_path.write_text(new_scanner, encoding='utf-8')
    print(f'Patched: {strong_count} SB, {watch_count} Watch')
    print(f'Scanner.html updated ({len(new_scanner)} bytes)')

    for s in rows[:3]:
        print(f'  {s["ticker"]}: ${s["price"]}, {s["days_left"]}d')
except Exception as e:
    print(f'ERROR: {e}')
    import traceback; traceback.print_exc()
    scanner_path.write_text(original_scanner, encoding='utf-8')
