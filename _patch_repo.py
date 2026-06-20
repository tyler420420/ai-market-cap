import json, re
from pathlib import Path

today_path = Path('ai_earnings_today.html')
scanner_path = Path('scanner.html')
backup = scanner_path.read_text(encoding='utf-8')

try:
    today_html = today_path.read_text(encoding='utf-8')
    scanner = scanner_path.read_text(encoding='utf-8')

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

    # Build fresh banners
    pick_color = '#00ff88' if pick['score'] >= 80 else '#58a6ff'
    ai_banner = (
        '<div class=pick-banner style="background:#161b22;border:2px solid #2ea043;border-radius:10px;padding:40px 18px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:15px 0;min-height:120px;box-shadow:0 0 20px rgba(46,160,67,0.4)">'
        '<span style="font-size:1.3em;color:#2ea043;font-weight:bold">&#9733; AI\'s Suggested Trade</span>'
        '<span style="font-size:1.2em;font-weight:bold;color:#fff">' + pick['ticker'] + '</span>'
        '<span style="font-size:0.95em;color:#fff">' + pick['company_name'][:28] + ('...' if len(pick['company_name']) > 28 else '') + '</span>'
        '<span style="font-size:0.95em;color:#fff">Score: <strong style="color:' + pick_color + '">' + str(round(pick['score'])) + '</strong></span>'
        '<span style="font-size:0.95em;color:#fff">Buy Price: <strong style="color:#00ff88">$' + str(int(pick['price'])) + '</strong></span>'
        '<span style="font-size:1em;color:#00ff88;font-weight:bold">Enter now - ' + ('Today' if pick['days_left'] == 0 else str(pick['days_left'])) + ' days to earnings</span>'
        '<a href="https://invite.kraken.com/JDNW/dq0q352v" target="_blank" style="display:inline-block;background:#5741d9;color:#fff;padding:8px 18px;border-radius:6px;font-weight:bold;text-decoration:none;font-size:0.9em;margin-left:auto">Trade ' + pick['ticker'] + ' on Kraken</a>'
        '</div>'
    )

    if pick2:
        p2c = '#00ff88' if pick2['score'] >= 80 else '#58a6ff'
        runner_banner = (
            '<div class=pick-banner style="background:#161b22;border:2px solid #1f6feb;border-radius:10px;padding:40px 18px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:0 0 15px;min-height:120px;box-shadow:0 0 20px rgba(31,111,235,0.4)">'
            '<span style="font-size:1.3em;color:#58a6ff;font-weight:bold">&#9733; Runner-Up Pick</span>'
            '<span style="font-size:1.2em;font-weight:bold;color:#fff">' + pick2['ticker'] + '</span>'
            '<span style="font-size:0.95em;color:#fff">' + pick2['company_name'][:28] + ('...' if len(pick2['company_name']) > 28 else '') + '</span>'
            '<span style="font-size:0.95em;color:#fff">Score: <strong style="color:' + p2c + '">' + str(round(pick2['score'])) + '</strong></span>'
            '<span style="font-size:0.95em;color:#fff">Buy Price: <strong style="color:#58a6ff">$' + str(int(pick2['price'])) + '</strong></span>'
            '<span style="font-size:1em;color:#58a6ff;font-weight:bold">Enter now - ' + ('Today' if pick2['days_left'] == 0 else str(pick2['days_left'])) + ' days to earnings</span>'
            '<a href="https://invite.kraken.com/JDNW/dq0q352v" target="_blank" style="display:inline-block;background:#5741d9;color:#fff;padding:8px 18px;border-radius:6px;font-weight:bold;text-decoration:none;font-size:0.9em;margin-left:auto">Trade ' + pick2['ticker'] + ' on Kraken</a>'
            '</div>'
        )
    else:
        runner_banner = ''

    # Find and replace banners
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

    ai_start = scanner.find("AI's Suggested Trade")
    if ai_start < 0: ai_start = scanner.find("AI&#39;s Suggested Trade")
    ai_div_start = scanner.rfind('<div', 0, ai_start)
    ai_div_end = find_div_end(scanner, ai_div_start)

    runner_start = scanner.find("Runner-Up Pick")
    if runner_start >= 0:
        r_div_start = scanner.rfind('<div', 0, runner_start)
        r_div_end = find_div_end(scanner, r_div_start)
    else:
        r_div_start = r_div_end = -1

    scanner = scanner[:ai_div_start] + ai_banner + scanner[ai_div_end:]
    if r_div_start >= 0 and r_div_end > r_div_start:
        offset = len(ai_banner) - (ai_div_end - ai_div_start)
        scanner = scanner[:r_div_start + offset] + runner_banner + scanner[r_div_end + offset:]

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

    # counters
    scanner = re.sub(r'(<span style="font-weight:bold;color:#2ea043">)\d+(</span> <span style="color:#8b949e">Strong Buy</span>)', r'\g<1>' + str(strong_count) + r'\g<2>', scanner, count=1)
    scanner = re.sub(r'(<span style="font-weight:bold;color:#58a6ff">)\d+(</span> <span style="color:#8b949e">Watch</span>)', r'\g<1>' + str(watch_count) + r'\g<2>', scanner, count=1)

    scanner_path.write_text(scanner, encoding='utf-8')
    print(f'scanner.html updated: {strong_count} SB, {watch_count} Watch')
    print(f'Size: {len(scanner)} bytes')

except Exception as e:
    print(f'ERROR: {e}')
    import traceback; traceback.print_exc()
    scanner_path.write_text(backup, encoding='utf-8')
