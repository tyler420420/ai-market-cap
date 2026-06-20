import json, re
from pathlib import Path

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
    print(f'scanner.html: rowsData at {scan_idx}-{scan_end}')

    new_scanner = scanner_content[:scan_idx + 13] + fresh_rows + ';'

    rows = json.loads(fresh_rows)
    strong_count = sum(1 for r in rows if r.get('score', 0) >= 75)
    watch_count = sum(1 for r in rows if 70 <= r.get('score', 0) < 75)
    print(f'Computed: {strong_count} SB, {watch_count} Watch')

    # Strong Buy counter
    new_scanner = re.sub(
        r'(<span style="font-weight:bold;color:#2ea043">)\d+(</span> <span style="color:#8b949e">Strong Buy</span>)',
        r'\g<1>' + str(strong_count) + r'\g<2>',
        new_scanner, count=1)
    # Watch counter
    new_scanner = re.sub(
        r'(<span style="font-weight:bold;color:#58a6ff">)\d+(</span> <span style="color:#8b949e">Watch</span>)',
        r'\g<1>' + str(watch_count) + r'\g<2>',
        new_scanner, count=1)

    scanner_path.write_text(new_scanner, encoding='utf-8')
    print(f'DONE: scanner.html patched ({len(new_scanner)} bytes)')

    # Verify
    verify = scanner_path.read_text(encoding='utf-8')
    sb_match = re.search(r'font-weight:bold;color:#2ea043">(\d+)</span> <span style="color:#8b949e">Strong Buy', verify)
    w_match = re.search(r'font-weight:bold;color:#58a6ff">(\d+)</span> <span style="color:#8b949e">Watch', verify)
    print(f'Verified: SB={sb_match.group(1) if sb_match else "NOT FOUND"}, Watch={w_match.group(1) if w_match else "NOT FOUND"}')

    # Check rowsData was updated
    vidx = verify.find('var rowsData=')
    vend = verify.find(']', vidx + 13)
    # Check first ticker
    first_ticker = re.search(r'"ticker":\s*"([^"]+)"', verify[vidx:vidx+200])
    print(f'First ticker in patched: {first_ticker.group(1) if first_ticker else "N/A"}')

except Exception as e:
    print(f'ERROR: {e}')
    import traceback; traceback.print_exc()
    scanner_path.write_text(original_scanner, encoding='utf-8')
    print('Restored original scanner.html')
