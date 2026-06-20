import json, re, shutil

# Read fresh data
with open('scanner_data.json', encoding='utf-8') as f:
    data = json.load(f)

# Read the working backup (June 16)
with open(r'C:\Users\Tyler_AI\Desktop\test_scanner_backup_20260617.html', encoding='utf-8') as f:
    backup = f.read()

# === Rebuild scanner.html from working backup with fresh data ===

# 1. Static rows: rebuild from fresh data using the same HTML structure as backup
# Extract ONE sample row to get the exact HTML structure
tbody_start = backup.find('<tbody id="stockTableBody">')
tbody_end = backup.find('</tbody>')
sample_rows = backup[tbody_start+len('<tbody id="stockTableBody">'):tbody_end]
# Count rows in backup
row_count = sample_rows.count('<tr ')
print(f'Backup has {row_count} static rows')

# Build static rows from fresh data using the SAME structure
# Pattern: <tr style="background:rgba(...)"><td data-label="Ticker">...
# Extract the template from the first row
first_tr_start = sample_rows.find('<tr ')
first_tr_end = sample_rows.find('</tr>') + len('</tr>')
first_row = sample_rows[first_tr_start:first_tr_end]
print(f'First row template: {repr(first_row[:200])}')

def score_color(s):
    return '#00ff88' if s >= 80 else '#58a6ff'

def row_bg(s):
    return 'rgba(0,255,136,0.12)' if s >= 80 else 'rgba(31,111,235,0.12)'

def days_color(d):
    if d == 0: return '#ff4444'
    if d <= 7: return '#00ff88'
    return '#ffcc00'

def fmt_mktcap(v):
    if v >= 1000: return str(round(v/1000)) + ' T'
    if v >= 1: return str(round(v)) + ' B'
    return str(round(v*1000)) + ' M'

def truncate(text, max_len=35):
    if len(text) > max_len:
        return text[:max_len] + '...'
    return text

def news_truncate(title):
    if not title: return ''
    if len(title) > 45:
        sp = title[:45].rfind(' ')
        if sp > 20:
            return title[:sp] + '...'
        return title[:45] + '...'
    return title

def sent_badge(sent):
    if sent == 'Positive':
        return '<span style="background:#1a2a1a;border:1px solid #2ea043;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#00ff88">Positive</span>'
    elif sent == 'Negative':
        return '<span style="background:#2a1a1a;border:1px solid #ff4444;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#ff6b6b">Negative</span>'
    elif sent == 'Mixed':
        return '<span style="background:#2a2a1a;border:1px solid #ffd700;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#ffd700">Mixed</span>'
    return '—'

static_rows = ''
for r in data:
    s = r['score']
    bg = row_bg(s)
    c = score_color(s)
    d = days_color(r['days_left'])
    days_str = 'Today' if r['days_left'] == 0 else str(r['days_left']) + 'd'
    sent = sent_badge(r.get('sentiment', ''))
    news = r.get('news') or {}
    news_url = news.get('url', '')
    news_title = news_truncate(news.get('title', ''))
    if news_url and news_title:
        news_cell = f'<a href="{news_url}" target="_blank" style="color:#fff;text-decoration:none">{news_title}</a>'
    elif news_title:
        news_cell = f'<span style="color:#fff">{news_title}</span>'
    else:
        news_cell = ''

    row = (
        f'<tr style="background:{bg}">'
        f'<td data-label="Ticker"><strong><a href="https://finance.yahoo.com/quote/{r["ticker"]}" target="_blank" style="color:#66b2ff">{r["ticker"]}</a></strong></td>'
        f'<td data-label="Company">{truncate(r["company_name"])}</td>'
        f'<td data-label="Score"><strong style="color:{c}">{r["score"]}</strong></td>'
        f'<td data-label="Earnings">{r["earnings_date"]}</td>'
        f'<td data-label="Days"><span style="color:{d};font-weight:bold">{days_str}</span></td>'
        f'<td data-label="Price" style="font-weight:bold">${int(r["price"])}</td>'
        f'<td data-label="3 Day"><span style="font-weight:bold">${int(r["pe_target"])}</span><br><span style="color:#00ff88">+{r["pe_upside"]}%</span></td>'
        f'<td data-label="7 Day">${int(r["3d"])}<br><span style="color:#00ff88">+{r["3d_up"]}%</span></td>'
        f'<td data-label="14 Day">${int(r["5d"])}<br><span style="color:#00ff88">+{r["5d_up"]}%</span></td>'
        f'<td data-label="Analysts" style="color:#bf8fff">{r["analysts"]}</td>'
        f'<td data-label="Strong Buy" style="color:#00ff88">{r["sb"]}</td>'
        f'<td data-label="Buy" style="color:#58a6ff">{r["buy"]}</td>'
        f'<td data-label="Hold" style="color:#ffcc00">{r["hold"]}</td>'
        f'<td data-label="Sell" style="color:#ff6b6b">{r["sell"]}</td>'
        f'<td data-label="Mkt Cap">{fmt_mktcap(r["mktcap"])}</td>'
        f'<td data-label="Shorts" style="color:#fff">{r["short_int"]}%</td>'
        f'<td data-label="IV" style="color:#fff">{r["iv"]}%</td>'
        f'<td data-label="Trend">{sent}</td>'
        f'<td data-label="News">{news_cell}</td>'
        f'</tr>'
    )
    static_rows += row

# 2. Build the HTML: header + table + static rows + JS
# Split backup at the tbody boundary
header_end = backup.find('<tbody id="stockTableBody">') + len('<tbody id="stockTableBody">')
footer_start = backup.find('</tbody>') + len('</tbody>')

header = backup[:header_end]
footer = backup[footer_start:]

# 3. Find the JS block location (after </table>)
table_close = footer.find('</table>')
js_position = footer.find('<script>', table_close)

header_and_table = header + static_rows + footer[table_close:js_position]
js_block_raw = footer[js_position:]

# 4. Replace rowsData with fresh data
# Find rowsData= line
rows_data_start = js_block_raw.find('var rowsData=')
rows_data_line_end = js_block_raw.find(';', rows_data_start) + 1
new_rows_data = 'var rowsData=' + json.dumps(data, ensure_ascii=False) + ';'
new_js_block = js_block_raw[:rows_data_start] + new_rows_data + js_block_raw[rows_data_line_end:]

html = header_and_table + new_js_block

# 5. Save
with open('scanner.html', 'w', encoding='utf-8') as f:
    f.write(html)
shutil.copy('scanner.html', r'C:\Users\Tyler_AI\Desktop\test_scanner.html')

print(f'Built scanner.html: {len(html)} bytes, {len(data)} stocks')
print(f'Top 3: {data[0]["ticker"]} ({data[0]["score"]}), {data[1]["ticker"]} ({data[1]["score"]}), {data[2]["ticker"]} ({data[2]["score"]})')

# 6. Verify static rows have double-quoted attrs
single_q = re.findall(r"style='[^']*'", static_rows)
print(f'Single-quote style attrs in static rows: {len(single_q)}')
if single_q:
    for m in single_q[:3]:
        print(f'  WARNING: {m[:80]}')
else:
    print('  Clean - all double-quoted')
