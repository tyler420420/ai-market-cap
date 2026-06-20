import json, re
from pathlib import Path

today_path = Path('ai_earnings_today.html')
scanner_path = Path('scanner.html')

backup = scanner_path.read_text(encoding='utf-8')

try:
    today_html = today_path.read_text(encoding='utf-8')
    idx = today_html.find('var rowsData=')
    arr_depth, end = 0, idx
    for i in range(idx + 13, len(today_html)):
        if today_html[i] == '[': arr_depth += 1
        elif today_html[i] == ']':
            arr_depth -= 1
            if arr_depth == 0: end = i; break
    fresh_rows_js = today_html[idx + 13:end + 1]

    tbody_match = re.search(r'<tbody[^>]*id="stockTableBody"[^>]*>(.*?)</tbody>', today_html, re.DOTALL)
    if not tbody_match:
        print('ERROR: No tbody found'); exit()
    fresh_tbody = tbody_match.group(1)
    print(f'Fresh: rowsData={len(fresh_rows_js)} bytes, tbody rows={fresh_tbody.count("<tr")}')

    scanner = scanner_path.read_text(encoding='utf-8')

    scan_idx = scanner.find('var rowsData=')
    arr_depth, scan_end = 0, scan_idx
    for i in range(scan_idx + 13, len(scanner)):
        if scanner[i] == '[': arr_depth += 1
        elif scanner[i] == ']':
            arr_depth -= 1
            if arr_depth == 0: scan_end = i; break
    scanner = scanner[:scan_idx + 13] + fresh_rows_js + ';' + scanner[scan_end + 1:]

    scanner = re.sub(
        r'<tbody[^>]*id="stockTableBody"[^>]*>.*?</tbody>',
        '<tbody id="stockTableBody">' + fresh_tbody + '</tbody>',
        scanner, count=1, flags=re.DOTALL)

    rows = json.loads(fresh_rows_js)
    strong_count = sum(1 for r in rows if r.get('score', 0) >= 75)
    watch_count = sum(1 for r in rows if 70 <= r.get('score', 0) < 75)
    scanner = re.sub(r'(<span style="font-weight:bold;color:#2ea043">)\d+(</span> <span style="color:#8b949e">Strong Buy</span>)', r'\g<1>' + str(strong_count) + r'\g<2>', scanner, count=1)
    scanner = re.sub(r'(<span style="font-weight:bold;color:#58a6ff">)\d+(</span> <span style="color:#8b949e">Watch</span>)', r'\g<1>' + str(watch_count) + r'\g<2>', scanner, count=1)

    scanner_path.write_text(scanner, encoding='utf-8')
    print(f'scanner.html updated: {strong_count} SB, {watch_count} Watch')

    verify = scanner_path.read_text(encoding='utf-8')
    tbody_m = re.search(r'<tbody[^>]*id="stockTableBody"[^>]*>(.*?)</tbody>', verify, re.DOTALL)
    if tbody_m:
        first_row = re.search(r'<tr[^>]*>(.*?)</tr>', tbody_m.group(1), re.DOTALL)
        if first_row:
            t = re.search(r'>([A-Z]{1,5})</a>', first_row.group(1))
            p = re.search(r'\$([0-9,.]+)', first_row.group(1))
            d = re.search(r'(\d+)d', first_row.group(1))
            print(f'First row: {t.group(1)} ${p.group(1)} {d.group(1)}d')
except Exception as e:
    print(f'ERROR: {e}')
    import traceback; traceback.print_exc()
    scanner_path.write_text(backup, encoding='utf-8')
