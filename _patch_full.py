import json, re
from pathlib import Path

today_path = Path('ai_earnings_today.html')
scanner_path = Path(r'C:\Users\Tyler_AI\Desktop\test_scanner.html')
backup = scanner_path.read_text(encoding='utf-8')

try:
    today_html = today_path.read_text(encoding='utf-8')
    scanner = scanner_path.read_text(encoding='utf-8')

    # === Extract fresh data ===
    idx = today_html.find('var rowsData=')
    arr_depth, end = 0, idx
    for i in range(idx + 13, len(today_html)):
        if today_html[i] == '[': arr_depth += 1
        elif today_html[i] == ']':
            arr_depth -= 1
            if arr_depth == 0: end = i; break
    fresh_rows_js = today_html[idx + 13:end + 1]
    rows = json.loads(fresh_rows_js)

    # Get AI pick and runner-up from fresh data
    pick = rows[0]  # First stock = AI pick
    pick2 = rows[1] if len(rows) > 1 else None  # Second = runner-up

    strong_count = sum(1 for r in rows if r.get('score', 0) >= 75)
    watch_count = sum(1 for r in rows if 70 <= r.get('score', 0) < 75)

    print(f'AI Pick: {pick["ticker"]} @ ${pick["price"]}, {pick["days_left"]}d, score={pick["score"]}')
    if pick2:
        print(f'Runner-Up: {pick2["ticker"]} @ ${pick2["price"]}, {pick2["days_left"]}d, score={pick2["score"]}')

    # === Build fresh AI pick banner ===
    pick_color = '#00ff88' if pick['score'] >= 80 else '#58a6ff'
    days_label = 'Today' if pick['days_left'] == 0 else str(pick['days_left'])
    ai_banner = (
        '<div class=pick-banner style="background:#161b22;border:2px solid #2ea043;border-radius:10px;padding:40px 18px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:15px 0;min-height:120px;box-shadow:0 0 20px rgba(46,160,67,0.4)">'
        '<span style="font-size:1.3em;color:#2ea043;font-weight:bold">&#9733; AI\'s Suggested Trade</span>'
        '<span style="font-size:1.2em;font-weight:bold;color:#fff">' + pick['ticker'] + '</span>'
        '<span style="font-size:0.95em;color:#fff">' + pick['company_name'][:28] + ('...' if len(pick['company_name']) > 28 else '') + '</span>'
        '<span style="font-size:0.95em;color:#fff">Score: <strong style="color:' + pick_color + '">' + str(round(pick['score'])) + '</strong></span>'
        '<span style="font-size:0.95em;color:#fff">Buy Price: <strong style="color:#00ff88">$' + str(int(pick['price'])) + '</strong></span>'
        '<span style="font-size:1em;color:#00ff88;font-weight:bold">Enter now - ' + days_label + ' days to earnings</span>'
        '<a href="https://invite.kraken.com/JDNW/dq0q352v" target="_blank" style="display:inline-block;background:#5741d9;color:#fff;padding:8px 18px;border-radius:6px;font-weight:bold;text-decoration:none;font-size:0.9em;margin-left:auto">Trade ' + pick['ticker'] + ' on Kraken</a>'
        '</div>'
    )

    # === Build fresh Runner-Up banner ===
    if pick2:
        pick2_color = '#00ff88' if pick2['score'] >= 80 else '#58a6ff'
        days2_label = 'Today' if pick2['days_left'] == 0 else str(pick2['days_left'])
        runner_banner = (
            '<div class=pick-banner style="background:#161b22;border:2px solid #1f6feb;border-radius:10px;padding:40px 18px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:0 0 15px;min-height:120px;box-shadow:0 0 20px rgba(31,111,235,0.4)">'
            '<span style="font-size:1.3em;color:#58a6ff;font-weight:bold">&#9733; Runner-Up Pick</span>'
            '<span style="font-size:1.2em;font-weight:bold;color:#fff">' + pick2['ticker'] + '</span>'
            '<span style="font-size:0.95em;color:#fff">' + pick2['company_name'][:28] + ('...' if len(pick2['company_name']) > 28 else '') + '</span>'
            '<span style="font-size:0.95em;color:#fff">Score: <strong style="color:' + pick2_color + '">' + str(round(pick2['score'])) + '</strong></span>'
            '<span style="font-size:0.95em;color:#fff">Buy Price: <strong style="color:#58a6ff">$' + str(int(pick2['price'])) + '</strong></span>'
            '<span style="font-size:1em;color:#58a6ff;font-weight:bold">Enter now - ' + days2_label + ' days to earnings</span>'
            '<a href="https://invite.kraken.com/JDNW/dq0q352v" target="_blank" style="display:inline-block;background:#5741d9;color:#fff;padding:8px 18px;border-radius:6px;font-weight:bold;text-decoration:none;font-size:0.9em;margin-left:auto">Trade ' + pick2['ticker'] + ' on Kraken</a>'
            '</div>'
        )
    else:
        runner_banner = ''

    # === Patch scanner.html ===

    # 1. Find and replace AI pick div
    ai_start = scanner.find("AI's Suggested Trade")
    if ai_start < 0:
        ai_start = scanner.find("AI&#39;s Suggested Trade")
    ai_div_start = scanner.rfind('<div', 0, ai_start)

    def find_div_end(html, start):
        depth = 1; i = start + 4
        while depth > 0 and i < len(html):
            if html[i:i+5] == '<div ' or html[i:i+4] == '<div>':
                depth += 1; i += 4
            elif html[i:i+6] == '</div>':
                depth -= 1
                if depth == 0: return i + 6
                i += 6
            else: i += 1
        return len(html)

    ai_div_end = find_div_end(scanner, ai_div_start)
    print(f'AI pick div: {ai_div_start}-{ai_div_end}')

    # 2. Find and replace runner-up div
    runner_start = scanner.find("Runner-Up Pick")
    if runner_start >= 0:
        runner_div_start = scanner.rfind('<div', 0, runner_start)
        runner_div_end = find_div_end(scanner, runner_div_start)
        print(f'Runner-up div: {runner_div_start}-{runner_div_end}')
    else:
        print('No runner-up found')
        runner_div_start = runner_div_end = -1

    # Replace AI pick
    scanner = scanner[:ai_div_start] + ai_banner + scanner[ai_div_end:]

    # Adjust runner-up position after replacement
    if runner_div_start > ai_div_start:
        offset = len(ai_banner) - (ai_div_end - ai_div_start)
        runner_div_start += offset
        runner_div_end += offset

    # Replace runner-up
    if runner_div_start >= 0 and runner_div_end > runner_div_start:
        scanner = scanner[:runner_div_start] + runner_banner + scanner[runner_div_end:]

    # 3. Patch rowsData JS
    scan_idx = scanner.find('var rowsData=')
    arr_depth, scan_end = 0, scan_idx
    for i in range(scan_idx + 13, len(scanner)):
        if scanner[i] == '[': arr_depth += 1
        elif scanner[i] == ']':
            arr_depth -= 1
            if arr_depth == 0: scan_end = i; break
    scanner = scanner[:scan_idx + 13] + fresh_rows_js + ';' + scanner[scan_end + 1:]

    # 4. Patch tbody rows
    tbody_match = re.search(r'<tbody[^>]*id="stockTableBody"[^>]*>(.*?)</tbody>', scanner, re.DOTALL)
    if tbody_match:
        fresh_tbody_match = re.search(r'<tbody[^>]*id="stockTableBody"[^>]*>(.*?)</tbody>', today_html, re.DOTALL)
        if fresh_tbody_match:
            scanner = scanner[:tbody_match.start()] + '<tbody id="stockTableBody">' + fresh_tbody_match.group(1) + '</tbody>' + scanner[tbody_match.end():]
            print('tbody patched')

    # 5. Patch counters
    scanner = re.sub(r'(<span style="font-weight:bold;color:#2ea043">)\d+(</span> <span style="color:#8b949e">Strong Buy</span>)', r'\g<1>' + str(strong_count) + r'\g<2>', scanner, count=1)
    scanner = re.sub(r'(<span style="font-weight:bold;color:#58a6ff">)\d+(</span> <span style="color:#8b949e">Watch</span>)', r'\g<1>' + str(watch_count) + r'\g<2>', scanner, count=1)

    scanner_path.write_text(scanner, encoding='utf-8')
    print(f'\nDONE: test_scanner.html updated ({len(scanner)} bytes)')
    print(f'Counters: {strong_count} SB, {watch_count} Watch')

    # Verify banners
    verify = scanner_path.read_text(encoding='utf-8')
    ai = verify.find("AI's Suggested Trade")
    if ai >= 0:
        print('AI Pick found at:', ai)
        ticker_m = re.search(r'font-weight:bold;color:#fff">([A-Z]+)</span>', verify[ai:ai+300])
        price_m = re.search(r'Buy Price.*?\$(\d+)', verify[ai:ai+300])
        print('  Ticker:', ticker_m.group(1) if ticker_m else '?', 'Price:', price_m.group(1) if price_m else '?')
    run = verify.find("Runner-Up Pick")
    if run >= 0:
        ticker2 = re.search(r'font-weight:bold;color:#fff">([A-Z]+)</span>', verify[run:run+300])
        price2 = re.search(r'Buy Price.*?\$(\d+)', verify[run:run+300])
        print('Runner-Up:', ticker2.group(1) if ticker2 else '?', 'Price:', price2.group(1) if price2 else '?')

except Exception as e:
    print(f'ERROR: {e}')
    import traceback; traceback.print_exc()
    scanner_path.write_text(backup, encoding='utf-8')
    print('Restored backup')
