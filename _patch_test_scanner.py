import json, re
from pathlib import Path

today_path = Path('ai_earnings_today.html')
scanner_path = Path(r'C:\Users\Tyler_AI\Desktop\test_scanner.html')

# Backup
backup = scanner_path.read_text(encoding='utf-8')

try:
    # === PART 1: Extract fresh rowsData from today.html ===
    today_html = today_path.read_text(encoding='utf-8')
    idx = today_html.find('var rowsData=')
    arr_depth, end = 0, idx
    for i in range(idx + 13, len(today_html)):
        if today_html[i] == '[': arr_depth += 1
        elif today_html[i] == ']':
            arr_depth -= 1
            if arr_depth == 0: end = i; break
    fresh_rows_js = today_html[idx + 13:end + 1]
    print(f'Fresh rowsData: {len(fresh_rows_js)} bytes')

    # === PART 2: Extract fresh tbody rows from today.html ===
    tbody_match = re.search(r'<tbody[^>]*id="stockTableBody"[^>]*>(.*?)</tbody>', today_html, re.DOTALL)
    if not tbody_match:
        print('ERROR: No tbody found in today.html')
        exit()
    fresh_tbody = tbody_match.group(1)
    fresh_tr_count = fresh_tbody.count('<tr')
    print(f'Fresh tbody rows: {fresh_tr_count}')

    # === PART 3: Patch scanner.html ===
    scanner = scanner_path.read_text(encoding='utf-8')

    # Patch rowsData JS
    scan_idx = scanner.find('var rowsData=')
    arr_depth, scan_end = 0, scan_idx
    for i in range(scan_idx + 13, len(scanner)):
        if scanner[i] == '[': arr_depth += 1
        elif scanner[i] == ']':
            arr_depth -= 1
            if arr_depth == 0: scan_end = i; break
    scanner = scanner[:scan_idx + 13] + fresh_rows_js + ';' + scanner[scan_end + 1:]

    # Patch tbody rows
    scanner = re.sub(
        r'<tbody[^>]*id="stockTableBody"[^>]*>.*?</tbody>',
        '<tbody id="stockTableBody">' + fresh_tbody + '</tbody>',
        scanner,
        count=1,
        flags=re.DOTALL
    )

    # Patch counters
    rows = json.loads(fresh_rows_js)
    strong_count = sum(1 for r in rows if r.get('score', 0) >= 75)
    watch_count = sum(1 for r in rows if 70 <= r.get('score', 0) < 75)
    scanner = re.sub(
        r'(<span style="font-weight:bold;color:#2ea043">)\d+(</span> <span style="color:#8b949e">Strong Buy</span>)',
        r'\g<1>' + str(strong_count) + r'\g<2>',
        scanner, count=1)
    scanner = re.sub(
        r'(<span style="font-weight:bold;color:#58a6ff">)\d+(</span> <span style="color:#8b949e">Watch</span>)',
        r'\g<1>' + str(watch_count) + r'\g<2>',
        scanner, count=1)

    scanner_path.write_text(scanner, encoding='utf-8')
    print(f'DONE: test_scanner.html updated ({len(scanner)} bytes)')
    print(f'Counters: {strong_count} SB, {watch_count} Watch')

    # Verify tbody
    verify = scanner_path.read_text(encoding='utf-8')
    tbody_m = re.search(r'<tbody[^>]*id="stockTableBody"[^>]*>(.*?)</tbody>', verify, re.DOTALL)
    if tbody_m:
        trs = re.findall(r'<tr', tbody_m.group(1))
        print(f'Verified tbody rows: {len(trs)}')
        # Show first row ticker
        first_row = re.search(r'<tr[^>]*>(.*?)</tr>', tbody_m.group(1), re.DOTALL)
        if first_row:
            ticker_m = re.search(r'>([A-Z]{1,5})</a>', first_row.group(1))
            price_m = re.search(r'\$([0-9,.]+)', first_row.group(1))
            days_m = re.search(r'(\d+)d', first_row.group(1))
            print(f'First ticker: {ticker_m.group(1) if ticker_m else "?"}, price: ${price_m.group(1) if price_m else "?"}, days: {days_m.group(1) if days_m else "?"}d')

except Exception as e:
    print(f'ERROR: {e}')
    import traceback; traceback.print_exc()
    scanner_path.write_text(backup, encoding='utf-8')
    print('Restored backup')
