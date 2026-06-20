import json

# Read the data
with open('scanner_data.json', encoding='utf-8') as f:
    data = json.load(f)

# Build a clean, standalone HTML with data embedded
html = '''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>AI Market Cap</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Segoe UI,Arial,sans-serif;background:#0d1117;color:#c9d1d9;padding:20px}
.header{background:linear-gradient(135deg,#1a1f2e,#161b22);padding:25px;border-radius:12px;margin-bottom:20px;border:1px solid #30363d}
.hdr-row{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:15px}
h1{color:#fff;font-size:1.8em;margin-bottom:5px}
.desc{color:#8b949e;font-size:0.95em}
.btn{background:#ffd700;border:2px solid #fff;color:#000;padding:10px 22px;border-radius:6px;font-size:0.9em;cursor:pointer;font-weight:bold;flex-shrink:0}
.btn:hover{background:#2ea043}
#refreshBtn{background:#1f6feb;border-color:#fff}
#refreshBtn:hover{background:#388bfd}
.updated{color:#8b949e;font-size:0.85em;margin-bottom:15px;text-align:right}
#stockTable{width:100%;max-width:1400px;border-collapse:collapse;margin-bottom:20px}
#stockTable thead th{background:#1a1f2e;color:#58a6ff;padding:12px 8px;border:1px solid #30363d;font-size:0.88em;text-align:left;cursor:pointer;user-select:none;white-space:nowrap}
#stockTable thead th:hover{background:#21262d}
#stockTable thead th.sorted-asc:after{content:" \\2191"}
#stockTable thead th.sorted-desc:after{content:" \\2193"}
#stockTable tbody tr{background:#161b22;border:1px solid #30363d;border-radius:4px;margin-bottom:4px;transition:background .15s}
#stockTable tbody tr:hover{background:#1c2128}
.score-high{background:rgba(0,255,136,0.12)}
.score-mid{background:rgba(31,111,235,0.12)}
#stockTable td{padding:10px 8px;border:1px solid #30363d;font-size:0.88em;vertical-align:middle}
.ticker a{color:#66b2ff;font-weight:bold;font-size:1em}
.score{font-weight:bold;font-size:1.3em}
.score-green{color:#00ff88}
.score-blue{color:#58a6ff}
.earn-cell{white-space:pre-line;font-size:0.85em}
.days{font-weight:bold}
.days-today{color:#ff4444}
.days-week{color:#00ff88}
.days-soon{color:#ffcc00}
.news a{color:#fff;text-decoration:none;font-size:0.82em}
.news a:hover{color:#87CEEB}
.note{color:#8b949e;font-size:0.85em;margin-bottom:20px;border:1px solid #30363d;border-radius:8px;padding:12px;background:#161b22}
</style>
</head>
<body>
<div class="header">
  <div class="hdr-row">
    <div>
      <h1>AI Market Cap</h1>
      <div class="desc">Pre-Earnings Momentum Scanner for AI/Tech Stocks</div>
    </div>
    <div>
      <button class="btn" id="refreshBtn" onclick="location.reload(true)">Refresh Prices</button>
    </div>
  </div>
</div>
<div class="updated" id="lastUpdated">Loading...</div>
<table id="stockTable">
<thead>
<tr>
<th data-col="ticker">Ticker</th>
<th data-col="company_name">Company</th>
<th data-col="score">Score</th>
<th>Earnings</th>
<th data-col="days_left">Days</th>
<th>Price</th>
<th>PE Target</th>
<th>3-Day</th>
<th>5-Day</th>
<th data-col="analysts">An.</th>
<th>SB</th>
<th>Buy</th>
<th>Hold</th>
<th>Sell</th>
<th data-col="mktcap">Mkt Cap</th>
<th>Short Int</th>
<th>IV</th>
<th>Sentiment</th>
<th>News</th>
</tr>
</thead>
<tbody id="stockTableBody"></tbody>
</table>
<div class="note">Pre-earnings strategy: buy 1-14 days before, sell 1-5 days after positive earnings. Stop loss: 10% hard stop pre-earnings. Extended Hours ON on Kraken Pro.</div>
<script>
var rowsData = ''' + json.dumps(data, ensure_ascii=False) + ''';

function fmtMktcap(v) {
    if (v >= 1000) return Math.round(v / 1000) + ' T';
    if (v >= 1) return Math.round(v) + ' B';
    return Math.round(v * 1000) + ' M';
}

function scoreColor(s) {
    return s >= 80 ? '#00ff88' : '#58a6ff';
}

function newsHtml(n) {
    if (!n) return '';
    var u = n.url || '';
    var t = n.title || '';
    if (t.length > 45) {
        var sp = t.lastIndexOf(' ', 45);
        t = sp > 20 ? t.substring(0, sp) + '...' : t.substring(0, 45) + '...';
    }
    return u ? '<a href="' + u + '" target="_blank">' + t + '</a>' : '<span>' + t + '</span>';
}

function renderTable() {
    var tbody = document.getElementById('stockTableBody');
    if (!tbody) return;
    var html = '';
    rowsData.forEach(function(r) {
        if (r.score < 50) return;
        var c = scoreColor(r.score);
        var bg = r.score >= 80 ? 'rgba(0,255,136,0.12)' : 'rgba(31,111,235,0.12)';
        var daysClass = r.days_left == 0 ? 'days-today' : (r.days_left <= 7 ? 'days-week' : 'days-soon');
        var daysText = r.days_left == 0 ? 'Today' : r.days_left + 'd';
        var sent = r.sentiment || '';
        var sentHtml = '';
        if (sent === 'Positive') sentHtml = '<span style="background:#1a2a1a;border:1px solid #2ea043;border-radius:5px;padding:2px 8px;font-size:0.75em;color:#00ff88">Positive</span>';
        else if (sent === 'Negative') sentHtml = '<span style="background:#2a1a1a;border:1px solid #ff4444;border-radius:5px;padding:2px 8px;font-size:0.75em;color:#ff6b6b">Negative</span>';
        else if (sent === 'Mixed') sentHtml = '<span style="background:#2a2a1a;border:1px solid #ffd700;border-radius:5px;padding:2px 8px;font-size:0.75em;color:#ffd700">Mixed</span>';
        else sentHtml = '—';

        html += '<tr class="' + (r.score >= 80 ? 'score-high' : 'score-mid') + '">';
        html += '<td class="ticker"><a href="https://finance.yahoo.com/quote/' + r.ticker + '" target="_blank">' + r.ticker + '</a></td>';
        html += '<td>' + r.company_name.substring(0, 35) + (r.company_name.length > 35 ? '...' : '') + '</td>';
        html += '<td class="score" style="color:' + c + '">' + r.score + '</td>';
        html += '<td class="earn-cell">' + r.earnings_date + '</td>';
        html += '<td class="days ' + daysClass + '">' + daysText + '</td>';
        html += '<td>$' + Math.floor(r.price) + '</td>';
        html += '<td>$' + Math.floor(r.pe_target) + ' | +' + r.pe_upside + '%</td>';
        html += '<td>$' + Math.floor(r['3d']) + ' | +' + r['3d_up'] + '%</td>';
        html += '<td>$' + Math.floor(r['5d']) + ' | +' + r['5d_up'] + '%</td>';
        html += '<td>' + r.analysts + '</td>';
        html += '<td style="color:#00ff88">' + r.sb + '</td>';
        html += '<td style="color:#58a6ff">' + r.buy + '</td>';
        html += '<td style="color:#ffcc00">' + r.hold + '</td>';
        html += '<td style="color:#ff6b6b">' + r.sell + '</td>';
        html += '<td>' + fmtMktcap(r.mktcap) + '</td>';
        html += '<td>' + r.short_int + '%</td>';
        html += '<td>' + r.iv + '%</td>';
        html += '<td>' + sentHtml + '</td>';
        html += '<td class="news">' + newsHtml(r.news) + '</td>';
        html += '</tr>';
    });
    tbody.innerHTML = html;
}

// Sort
var sortCol = 'score';
var sortAsc = false;

function getVal(r, col) {
    var m = {
        'ticker': r.ticker, 'company_name': r.company_name, 'score': r.score,
        'days_left': r.days_left, 'analysts': r.analysts, 'mktcap': r.mktcap,
        'short_int': r.short_int, 'iv': r.iv
    };
    return m[col] || r[col] || 0;
}

function updateArrows() {
    document.querySelectorAll('th[data-col]').forEach(function(th) {
        th.classList.remove('sorted-asc', 'sorted-desc');
    });
    var th = document.querySelector('th[data-col="' + sortCol + '"]');
    if (th) th.classList.add(sortAsc ? 'sorted-asc' : 'sorted-desc');
}

function sortBy(col) {
    if (sortCol === col) sortAsc = !sortAsc;
    else {
        sortCol = col;
        sortAsc = ['ticker', 'company_name'].indexOf(col) >= 0;
    }
    rowsData.sort(function(a, b) {
        var va = getVal(a, col), vb = getVal(b, col);
        if (typeof va === 'number') return sortAsc ? va - vb : vb - va;
        return sortAsc ? String(va).localeCompare(String(vb)) : String(vb).localeCompare(String(va));
    });
    renderTable();
    updateArrows();
}

// Header click sort
document.querySelectorAll('th[data-col]').forEach(function(th) {
    th.addEventListener('click', function() { sortBy(th.getAttribute('data-col')); });
});

// Init
var now = new Date();
var pt = new Date(now.toLocaleString('en-US', {timeZone: 'America/Los_Angeles'}));
var ts = pt.toLocaleString('en-US', {timeZone: 'America/Los_Angeles', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit', hour12: true});
document.getElementById('lastUpdated').textContent = 'Last Updated: ' + ts + ' PT';
sortBy('score');
</script>
</body>
</html>'''

with open('test_scanner.html', 'w', encoding='utf-8') as f:
    f.write(html)

# Also save to Desktop
import shutil
shutil.copy('test_scanner.html', r'C:\Users\Tyler_AI\Desktop\test_scanner.html')

print(f'Built clean test_scanner.html with {len(data)} stocks')
print(f'Top 3: {data[0]["ticker"]} ({data[0]["score"]}), {data[1]["ticker"]} ({data[1]["score"]}), {data[2]["ticker"]} ({data[2]["score"]})')
print(f'File size: {len(html)} bytes')
