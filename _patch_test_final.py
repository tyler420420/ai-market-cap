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

    pick = rows[0]
    pick2 = rows[1] if len(rows) > 1 else None
    strong_count = sum(1 for r in rows if r.get('score', 0) >= 75)
    watch_count = sum(1 for r in rows if 70 <= r.get('score', 0) < 75)

    print(f'AI Pick: {pick["ticker"]} ${pick["price"]} | Runner: {pick2["ticker"] if pick2 else "N/A"}')

    # === Extract DRAM price from today.html ===
    # Find the container that has TRENDING ETF and extract the price div
    dram_label_idx = today_html.find('TRENDING ETF')
    # Find the price div: <div style="color:#fff;font-size:0.68em">$PRICE</div>
    dram_price_match = re.search(r'(<div style="color:#fff;font-size:0\.68em">)\$[\d.]+(</div>)', today_html[dram_label_idx:dram_label_idx+300])
    if dram_price_match:
        today_dram_price = today_html[dram_label_idx + dram_price_match.start():dram_label_idx + dram_price_match.end()]
        print(f'DRAM price from today.html: {today_dram_price}')
    else:
        print('WARNING: Could not find DRAM price in today.html')
        today_dram_price = None

    # === Build fresh banners ===
    def build_banner(ticker, company, score, price, days, label, badge_color, border_color, shadow_color):
        c = '#00ff88' if score >= 80 else '#58a6ff'
        d = 'Today' if days == 0 else str(days)
        return (
            '<div class=pick-banner style="background:#161b22;border:2px solid ' + border_color + ';border-radius:10px;padding:40px 18px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:15px 0;min-height:120px;box-shadow:0 0 20px rgba(' + shadow_color + ',0.4)">'
            '<span style="font-size:1.3em;color:' + badge_color + ';font-weight:bold">&#9733; ' + label + '</span>'
            '<span style="font-size:1.2em;font-weight:bold;color:#fff">' + ticker + '</span>'
            '<span style="font-size:0.95em;color:#fff">' + company[:28] + ('...' if len(company) > 28 else '') + '</span>'
            '<span style="font-size:0.95em;color:#fff">Score: <strong style="color:' + c + '">' + str(round(score)) + '</strong></span>'
            '<span style="font-size:0.95em;color:#fff">Buy Price: <strong style="color:' + c + '">$' + str(int(price)) + '</strong></span>'
            '<span style="font-size:1em;color:' + c + ';font-weight:bold">Enter now - ' + d + ' days to earnings</span>'
            '<a href="https://invite.kraken.com/JDNW/dq0q352v" target="_blank" style="display:inline-block;background:#5741d9;color:#fff;padding:8px 18px;border-radius:6px;font-weight:bold;text-decoration:none;font-size:0.9em;margin-left:auto">Trade ' + ticker + ' on Kraken</a>'
            '</div>'
        )

    ai_banner = build_banner(pick['ticker'], pick['company_name'], pick['score'], pick['price'], pick['days_left'], "AI's Suggested Trade", '#2ea043', '#2ea043', '46,160,67')
    runner_banner = build_banner(pick2['ticker'], pick2['company_name'], pick2['score'], pick2['price'], pick2['days_left'], 'Runner-Up Pick', '#58a6ff', '#1f6feb', '31,111,235') if pick2 else ''

    # === Patch scanner.html ===
    def find_div_end(html, start):
        depth = 1; i = start + 4
        while depth > 0 and i < len(html):
            if html[i:i+5] == '<div ' or html[i:i+4] == '<div>': depth += 1; i += 4
            elif html[i:i+6] == '</div>':
                depth -= 1
                if depth == 0: return i + 6
                i += 6
            else: i += 1
        return len(html)

    # AI pick div
    ai_start = scanner.find("AI's Suggested Trade")
    if ai_start < 0: ai_start = scanner.find("AI&#39;s Suggested Trade")
    ai_div_s = scanner.rfind('<div', 0, ai_start)
    ai_div_e = find_div_end(scanner, ai_div_s)
    scanner = scanner[:ai_div_s] + ai_banner + scanner[ai_div_e:]

    # Runner-up div
    run_start = scanner.find("Runner-Up Pick")
    if run_start >= 0:
        r_div_s = scanner.rfind('<div', 0, run_start)
        r_div_e = find_div_end(scanner, r_div_s)
        scanner = scanner[:r_div_s] + runner_banner + scanner[r_div_e:]

    # DRAM price
    if today_dram_price:
        old_dram_pattern = re.search(r'<div style="color:#fff;font-size:0\.68em">\$[\d.]+</div>', scanner)
        if old_dram_pattern:
            scanner = scanner[:old_dram_pattern.start()] + today_dram_price + scanner[old_dram_pattern.end():]
            print(f'DRAM price updated: {today_dram_price}')
        else:
            print('WARNING: DRAM price pattern not found in scanner.html')
    else:
        print('WARNING: No DRAM price to update')

    # rowsData JS
    scan_idx = scanner.find('var rowsData=')
    arr_depth, scan_end = 0, scan_idx
    for i in range(scan_idx + 13, len(scanner)):
        if scanner[i] == '[': arr_depth += 1
        elif scanner[i] == ']':
            arr_depth -= 1
            if arr_depth == 0: scan_end = i; break
    scanner = scanner[:scan_idx + 13] + fresh_rows_js + ';' + scanner[scan_end + 1:]

    # tbody
    t = re.search(r'<tbody[^>]*id="stockTableBody"[^>]*>(.*?)</tbody>', scanner, re.DOTALL)
    ft = re.search(r'<tbody[^>]*id="stockTableBody"[^>]*>(.*?)</tbody>', today_html, re.DOTALL)
    if t and ft:
        scanner = scanner[:t.start()] + '<tbody id="stockTableBody">' + ft.group(1) + '</tbody>' + scanner[t.end():]
        print('tbody patched')

    # Counters
    scanner = re.sub(r'(<span style="font-weight:bold;color:#2ea043">)\d+(</span> <span style="color:#8b949e">Strong Buy</span>)', r'\g<1>' + str(strong_count) + r'\g<2>', scanner, count=1)
    scanner = re.sub(r'(<span style="font-weight:bold;color:#58a6ff">)\d+(</span> <span style="color:#8b949e">Watch</span>)', r'\g<1>' + str(watch_count) + r'\g<2>', scanner, count=1)

    scanner_path.write_text(scanner, encoding='utf-8')
    print(f'\nDONE: test_scanner.html ({len(scanner)} bytes)')

except Exception as e:
    print(f'ERROR: {e}')
    import traceback; traceback.print_exc()
    scanner_path.write_text(backup, encoding='utf-8')
