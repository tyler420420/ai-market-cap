"""Generate scanner.html - the permanent static shell.
Key: HTML is static and NEVER changes. Data comes from scanner_data.json."""
import json
import re

# Load current data for preview
with open('scanner_data.json', encoding='utf-8') as f:
    rows_data = json.load(f)

strong_buys = [s for s in rows_data if s['score'] >= 75]
strong_buys.sort(key=lambda x: -x.get('5d_up', 0))
pick = strong_buys[0] if strong_buys else (rows_data[0] if rows_data else None)
pick2 = strong_buys[1] if len(strong_buys) > 1 else None
strong_count = len([s for s in rows_data if s['score'] >= 75])
watch_count = len([s for s in rows_data if 50 <= s['score'] < 75])

# Build ticker strip
ticker_items = ''
for s in rows_data:
    if s['score'] < 50:
        continue
    chg = s.get('price_change_pct', 0)
    chg_cls = 'ticker-up' if chg >= 0 else 'ticker-dn'
    chg_str = '+' + f'{chg:.2f}%' if chg >= 0 else f'{chg:.2f}%'
    ticker_items += (
        '<span class=ticker-item>'
        '<span style="font-weight:bold;color:#00ff88">' + str(s['score']) + '</span>'
        ' <span class=ticker-sym>' + s['ticker'] + '</span>'
        ' <span class=ticker-price>$' + str(int(s['price'])) + '</span>'
        ' <span class="ticker-chg ' + chg_cls + '">' + chg_str + '</span>'
        '</span>'
    )
ticker_items += '<a href="https://invite.kraken.com/JDNW/dq0q352v" target="_blank" style="display:inline-flex;align-items:center;gap:6px;padding:0 18px;border-right:1px solid #30363d;flex-shrink:0;text-decoration:none"><span style="font-size:1em">&#x1F4B8;</span><span style="font-weight:bold;color:#00ff88;font-size:0.9em">$300 Sign Up Bonus</span><span style="font-weight:bold;color:#9333ea;font-size:0.9em">Trade On Kraken</span></a>'
ticker_strip = '<div class=ticker-strip><div class=ticker-strip-inner>' + ticker_items + ticker_items + '</div></div>'

# Buttons row
buttons_row = (
    '<div style="display:flex;flex-direction:column;gap:6px;align-items:flex-end;flex-shrink:0">'
    '<div style="display:flex;gap:6px;align-items:center">'
    '<a href="/about" style="background:#dc3545;color:#fff;padding:10px 18px;border-radius:6px;font-size:0.9em;text-decoration:none;font-weight:bold;border:1px solid #fff" onmouseover="this.style.background=\'#e84a5f\'" onmouseout="this.style.background=\'#dc3545\'">FAQ</a>'
    '<a href="/wins" style="background:#238636;color:#fff;padding:10px 18px;border-radius:6px;font-size:0.9em;text-decoration:none;font-weight:bold;border:1px solid #fff" onmouseover="this.style.background=\'#2ea043\'" onmouseout="this.style.background=\'#238636\'">Wins</a>'
    '<a href="/calendar" style="background:#1f6feb;color:#fff;padding:10px 18px;border-radius:6px;font-size:0.9em;text-decoration:none;font-weight:bold;border:1px solid #fff" onmouseover="this.style.background=\'#388bfd\'" onmouseout="this.style.background=\'#1f6feb\'">Calendar</a>'
    '<button class=btn id=scanBtn style="background:#ffd700;color:#000;font-weight:bold;border:1px solid #fff;cursor:pointer" onmouseover="this.style.background=\'#fff176\'" onmouseout="this.style.background=\'#ffd700\'" onclick=runScan()>PRO SCAN</button>'
    '</div>'
    '<div style="display:flex;gap:6px;align-items:center">'
    '<a href="https://x.com/AIMoneyMach" target="_blank" style="background:#5741d9;color:#fff;padding:3px 10px;border-radius:5px;border:1px solid #fff;font-size:0.82em;font-weight:bold;text-decoration:none" onmouseover="this.style.background=\'#6e55e0\'" onmouseout="this.style.background=\'#5741d9\'">Follow Us On X</a>'
    '<span style="background:#161b22;border:1px solid #2ea043;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#2ea043">' + str(strong_count) + '</span> <span style="color:#8b949e">Strong Buy</span></span>'
    '<span style="background:#161b22;border:1px solid #1f6feb;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#58a6ff">' + str(watch_count) + '</span> <span style="color:#8b949e">Watch</span></span>'
    '</div>'
    '</div>'
)

# IPO cards
ipo_cards = (
    '<div style="display:flex;gap:6px;align-items:center;justify-content:center;flex-wrap:wrap;max-width:800px;margin:0 auto">'
    '<div style="background:#0d1a0d;border:1px solid #2ea043;border-radius:8px;padding:8px 14px;min-width:140px;box-shadow:0 0 10px rgba(46,160,67,0.3)">'
    '<div style="color:#2ea043;font-size:0.65em;font-weight:bold;margin-bottom:2px">&#128293; SOONEST TOP IPO</div>'
    '<a href="https://www.prnewswire.com/news-releases/applied-aerospace--defense-inc-announces-launch-of-initial-public-offering-302781752.html" target="_blank" style="color:#00ff88;font-size:0.95em;font-weight:bold;text-decoration:none">Applied Aerospace</a>'
    '<div style="color:#fff;font-size:0.68em">Jun 03 | $634M</div></div>'
    '<div style="background:#0d1a0d;border:1px solid #1f6feb;border-radius:8px;padding:8px 14px;min-width:140px;box-shadow:0 0 10px rgba(31,111,235,0.3)">'
    '<div style="color:#1f6feb;font-size:0.65em;font-weight:bold;margin-bottom:2px">&#128293; NEXT TOP IPO</div>'
    '<a href="https://www.spacex.com/ipo" target="_blank" style="color:#00ff88;font-size:0.95em;font-weight:bold;text-decoration:none">SpaceX</a>'
    '<div style="color:#fff;font-size:0.68em">Jun 12 | $1.5T</div></div>'
    '<div style="background:#0d1a0d;border:1px solid #ffd700;border-radius:8px;padding:8px 14px;min-width:140px;box-shadow:0 0 10px rgba(255,215,0,0.2)">'
    '<div style="color:#ffd700;font-size:0.65em;font-weight:bold;margin-bottom:2px">&#128293; TOP IPO</div>'
    '<a href="https://discord.com/ipo" target="_blank" style="color:#00ff88;font-size:0.95em;font-weight:bold;text-decoration:none">Discord</a>'
    '<div style="color:#fff;font-size:0.68em">Sep 01 | $15B</div></div>'
    '<div style="background:#0d1428;border:1px solid #5741d9;border-radius:8px;padding:8px 14px;min-width:140px;box-shadow:0 0 10px rgba(87,65,217,0.3);margin-left:24px">'
    '<div style="color:#9333ea;font-size:0.65em;font-weight:bold;margin-bottom:2px">&#128293; TRENDING ETF</div>'
    '<a href="https://finance.yahoo.com/quote/DRAM/" target="_blank" style="color:#00ff88;font-size:0.95em;font-weight:bold;text-decoration:none">DRAM</a>'
    '<div style="color:#fff;font-size:0.68em" id=dram-price>Loading...</div></div>'
    '</div>'
)

header_html = (
    '<div class=header><div class=hdr-row>'
    '<div><a href="https://aismarketcap.com" style="color:#fff;text-decoration:none"><h1>AI Market Cap</h1></a><div style="color:#fff;font-size:0.95em">Pre-Earnings Tech Stock Scanner</div></div>'
    + ipo_cards
    + buttons_row
    + '</div></div>'
)

# AI pick banner
ai_pick_html = ''
if pick:
    pick_color = '#00ff88' if pick['score'] >= 80 else '#58a6ff'
    earn_label = 'Today' if pick['days_left'] == 0 else str(pick['days_left'])
    ai_pick_html = (
        '<div class=pick-banner id=ai-pick style="background:#161b22;border:2px solid #2ea043;border-radius:10px;padding:40px 18px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:15px 0;min-height:120px;box-shadow:0 0 20px rgba(46,160,67,0.4)">'
        '<span style="font-size:1.3em;color:#2ea043;font-weight:bold">&#9733; AI\'s Suggested Trade</span>'
        '<span style="font-size:1.2em;font-weight:bold;color:#fff">' + pick['ticker'] + '</span>'
        '<span style="font-size:0.95em;color:#fff">' + pick['company_name'][:28] + ('...' if len(pick['company_name']) > 28 else '') + '</span>'
        '<span style="font-size:0.95em;color:#fff">Score: <strong style="color:' + pick_color + '">' + str(pick['score']) + '</strong></span>'
        '<span style="font-size:0.95em;color:#fff">Buy Price: <strong style="color:#00ff88">$' + str(int(pick['price'])) + '</strong></span>'
        '<span style="font-size:1em;color:#00ff88;font-weight:bold">Enter now - ' + earn_label + ' days to earnings</span>'
        '<a href="https://invite.kraken.com/JDNW/dq0q352v" target="_blank" style="display:inline-block;background:#5741d9;color:#fff;padding:8px 18px;border-radius:6px;font-weight:bold;text-decoration:none;font-size:0.9em;margin-left:auto">Trade ' + pick['ticker'] + ' on Kraken</a>'
        '</div>'
    )

# Runner-up banner
ru_pick_html = ''
if pick2:
    earn_label2 = 'Today' if pick2['days_left'] == 0 else str(pick2['days_left'])
    ru_pick_html = (
        '<div class=pick-banner id=runner-up-pick style="background:#161b22;border:2px solid #1f6feb;border-radius:10px;padding:40px 18px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:0 0 15px;min-height:120px;box-shadow:0 0 20px rgba(31,111,235,0.4)">'
        '<span style="font-size:1.3em;color:#58a6ff;font-weight:bold">&#9733; Runner-Up Pick</span>'
        '<span style="font-size:1.2em;font-weight:bold;color:#fff">' + pick2['ticker'] + '</span>'
        '<span style="font-size:0.95em;color:#fff">' + pick2['company_name'][:28] + ('...' if len(pick2['company_name']) > 28 else '') + '</span>'
        '<span style="font-size:0.95em;color:#fff">Score: <strong style="color:#58a6ff">' + str(pick2['score']) + '</strong></span>'
        '<span style="font-size:0.95em;color:#fff">Buy Price: <strong style="color:#58a6ff">$' + str(int(pick2['price'])) + '</strong></span>'
        '<span style="font-size:1em;color:#58a6ff;font-weight:bold">Enter now - ' + earn_label2 + ' days to earnings</span>'
        '<a href="https://invite.kraken.com/JDNW/dq0q352v" target="_blank" style="display:inline-block;background:#5741d9;color:#fff;padding:8px 18px;border-radius:6px;font-weight:bold;text-decoration:none;font-size:0.9em;margin-left:auto">Trade ' + pick2['ticker'] + ' on Kraken</a>'
        '</div>'
    )

# Table headers
th_cols = [
    ('Ticker<br>Symbol', 'ticker'), ('Company<br>Name', 'company_name'), ('Overall<br>Score', 'score'),
    ('Earnings<br>Date', 'earnings_date'), ('Days<br>Left', 'days_left'), ('Current<br>Price', 'price'),
    ('3 Day<br>Target', 'pe_target'), ('7 Day<br>Target', '3d'), ('14 Day<br>Target', '5d'),
    ('Total<br>Analyst', 'analysts'), ('Strong<br>Buy', 'sb'), ('Buy<br>Ratings', 'buy'),
    ('Hold<br>Ratings', 'hold'), ('Sell<br>Ratings', 'sell'), ('Market<br>Cap', 'mktcap'),
    ('Total<br>Shorts', 'short_int'), ('Implied<br>Volatility', 'iv'),
    ('Earnings<br>Trend', 'sentiment'), ('Recent News', 'news')
]
ths = ''.join('<th data-col="' + col + '">' + label + '</th>' for label, col in th_cols)
table_header = '<table id="stockTable"><thead><tr>' + ths + '</tr></thead><tbody id="stockTableBody"></tbody></table>'

# Load CSS from existing HTML
with open('ai_earnings_today.html', encoding='utf-8') as f:
    c = f.read()
style_m = re.search(r'<style>(.*?)</style>', c, re.DOTALL)
css = style_m.group(1)

# Extract renderTable script from existing HTML
body_start = c.find('</head>') + 6
body_end = c.rfind('</html>')
body = c[body_start:body_end]
script_blocks = list(re.finditer(r'<script[^>]*>(.*?)</script>', body, re.DOTALL))
render_script = ''
for s in script_blocks:
    content = s.group(1)
    if 'rowsData' in content and 'renderTable' in content:
        render_script = content
        break

# Extract scan button script
scan_script = ''
chat_script = ''
chat_btn = ''
sub_popup_script = ''
note_html = ''
disclaimer_html = ''
for s in script_blocks:
    content = s.group(1)
    sn = s.group(0)
    if "scanBtn=document.getElementById" in content:
        scan_script = content
    if "chatOpen" in content and "chat-btn" in content:
        chat_script = content
    if 'id="chat-btn"' in sn:
        chat_btn = sn
    if 'sub-popup' in content and 'setTimeout' in content:
        sub_popup_script = content

# Note and disclaimer
note_m = re.search(r'<div class=note>.*?</div>', body, re.DOTALL)
disclaimer_m = re.search(r'<div class=disclaimer>.*?</div>', body, re.DOTALL)
if note_m:
    note_html = note_m.group(0)
if disclaimer_m:
    disclaimer_html = disclaimer_m.group(0)

# Build the JavaScript - replace hardcoded rowsData with a fetch call
# Find the var rowsData=...; line
rows_data_json = json.dumps(rows_data)
render_script_dyn = re.sub(
    r'var rowsData=.*?;(\s*var sortCol)',
    '''var rowsData = [];
var dataLoaded = false;

function loadData() {
    fetch('/data')
        .then(function(r) { return r.json(); })
        .then(function(d) {
            rowsData = d;
            dataLoaded = true;
            var updated = document.getElementById('lastUpdated');
            if (updated) {
                var now = new Date();
                var pt = new Date(now.toLocaleString('en-US', {timeZone: 'America/Los_Angeles'}));
                var ts = pt.toLocaleString('en-US', {timeZone: 'America/Los_Angeles', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit', hour12: true});
                updated.textContent = 'Last Updated: ' + ts + ' PT';
            }
            var dramRow = rowsData.find(function(r) { return r.ticker === 'DRAM'; });
            if (dramRow) {
                var dramEl = document.getElementById('dram-price');
                if (dramEl) dramEl.textContent = '$' + dramRow.price.toFixed(2);
            }
            renderTable();
            updateArrows();
        })
        .catch(function(e) {
            console.error('Failed to load data:', e);
            var tbody = document.getElementById('stockTableBody');
            if (tbody) {
                tbody.innerHTML = '<tr><td colspan="19" style="text-align:center;padding:30px;color:#ff6b6b">Failed to load data. Please refresh.</td></tr>';
            }
        });
}

document.addEventListener('DOMContentLoaded', loadData);\\1''',
    render_script,
    flags=re.DOTALL
)

# Build final HTML
html = (
    '<!DOCTYPE html><html><head>'
    '<meta charset="UTF-8"><title>AI Market Cap</title>'
    '<link rel="icon" type="image/x-icon" href="/favicon.ico">'
    '<meta name="description" content="AI pre-earnings momentum scanner for tech stocks. Track scores, analyst ratings, PE targets, and implied moves before earnings reports.">'
    '<meta property="og:title" content="AI Market Cap">'
    '<meta property="og:description" content="Pre-Earnings Tech Stock Scanner for AI stocks. Scores, PE targets, and 14-day implied moves before earnings reports.">'
    '<meta property="og:image" content="https://aismarketcap.com/static/logo.png">'
    '<meta property="og:url" content="https://aismarketcap.com">'
    '<meta property="og:type" content="website">'
    '<meta name="twitter:card" content="summary_large_image">'
    '<meta name="twitter:title" content="AI Market Cap">'
    '<meta name="twitter:description" content="Pre-earnings momentum scanner for AI/tech stocks. Track scores, analyst ratings, PE targets, and implied moves before earnings.">'
    '<meta name="twitter:image" content="https://aismarketcap.com/static/logo.png">'
    '<style>' + css + '</style>'
    '</head><body>'
    '<div id=sub-popup><div id=sub-popup-box><h2>Unlock Full Scanner Power</h2><p>Subscribe for 3 daily scans, real-time alerts, and the AI Chat Analyst.</p><div id=sub-popup-features><div><span>&#10003;</span> 3 daily scans</div><div><span>&#10003;</span> Real-time earnings alerts</div><div><span>&#10003;</span> AI Chat Analyst</div><div><span>&#10003;</span> Priority pre-earnings picks</div></div><a href="/pricing" id=sub-popup-btn>Subscribe Now</a><button id=sub-popup-close onclick="document.getElementById(\'sub-popup\').classList.remove(\'show\')">Maybe Later</button></div></div>'
    '<script>setTimeout(function(){if(!window.isSubscribed){document.getElementById("sub-popup").classList.add("show");}},300000)</script>'
    + ticker_strip
    + header_html
    + '<div class=warn id=warnMsg></div>'
    + ai_pick_html
    + ru_pick_html
    + table_header
    + '<div class=updated id=lastUpdated></div>'
    + note_html
    + disclaimer_html
    + '<script>' + render_script_dyn + '</script>'
    + ('<script>' + scan_script + '</script>' if scan_script else '')
    + chat_btn
    + ('<script>' + chat_script + '</script>' if chat_script else '')
    + '</body></html>'
)

with open('scanner.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('Generated scanner.html (' + str(len(html)) + ' bytes), ' + str(len(rows_data)) + ' stocks')
