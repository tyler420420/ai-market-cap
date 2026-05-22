content = open('ai_earnings_scanner.py', encoding='utf-8').read()

# 1. Fix header section - add sticky bar before ticker, fix title
old_hdr = """html += '<div class=header><div class=hdr-row><div><h1>' + SCANNER_TITLE + '</h1><div class=desc>Pre-earnings momentum scanner for Tech sector | Auto-runs daily at 6:30 AM PT | Subscribe to unlock Run Scan & Chat</div></div>'
html += '<div style="display:flex;flex-direction:column;gap:8px;align-items:flex-end;margin-left:auto">'
html += '<div style="display:flex;gap:6px;align-items:center"><span style="background:#161b22;border:1px solid #2ea043;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#2ea043">' + str(sbs) + '</span> <span style="color:#8b949e">Strong Buy</span></span><span style="background:#161b22;border:1px solid #1f6feb;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#58a6ff">' + str(watches) + '</span> <span style="color:#8b949e">Watch</span></span><button class=btn id=refreshBtn onclick=refreshData()>Refresh</button><button class=btn id=scanBtn onclick=runScan()>Run Scan</button></div></div></div></div><div class=warn id=warnMsg></div><div class=updated>Updated: ' + timestamp"""

new_hdr = """html += '<div style="background:#1a2a1a;border-bottom:2px solid #2ea043;padding:10px 20px;text-align:center;font-size:0.9em"><span style="color:#2ea043">&#10003;</span> Free scan runs daily at 6:30 AM PT &nbsp;|&nbsp; <a href="/pricing" style="color:#ffd700;font-weight:bold;text-decoration:none">Subscribe to run additional scans</a> &nbsp;|&nbsp; <a href="/pricing" style="color:#ffd700;text-decoration:none">+ AI Trading Chat Assistant</a></div>'
html += '<div class=header><div class=hdr-row><div><a href="https://aismarketcap.com" style="color:#58a6ff;text-decoration:none"><h1>AI Market Cap Scanner</h1></a><div class=desc>Pre-earnings momentum scanner for Tech sector</div></div>'
html += '<div style="display:flex;flex-direction:column;gap:8px;align-items:flex-end;margin-left:auto">'
html += '<div style="display:flex;gap:6px;align-items:center"><span style="background:#161b22;border:1px solid #2ea043;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#2ea043">' + str(sbs) + '</span> <span style="color:#8b949e">Strong Buy</span></span><span style="background:#161b22;border:1px solid #1f6feb;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#58a6ff">' + str(watches) + '</span> <span style="color:#8b949e">Watch</span></span><a href="/about" class="btn" style="background:#1a2a2a;border:1px solid #30363d;color:#58a6ff;padding:10px 18px;border-radius:6px;font-size:0.9em;text-decoration:none;font-weight:normal">How It Works</a><button class=btn id=refreshBtn onclick=refreshData()>Refresh</button><button class=btn id=scanBtn onclick=runScan()>Run Scan</button></div></div></div></div><div class=warn id=warnMsg></div><div class=updated>Last Updated: ' + timestamp"""

if old_hdr in content:
    content = content.replace(old_hdr, new_hdr)
    print('1. Header + sticky bar fixed')
else:
    print('1. NOT found')

# 2. Add meta tags in head
old_head = "html += '<title>' + SCANNER_TITLE + '</title><style>'"
new_head = """html += '<title>' + SCANNER_TITLE + '</title>'
html += '<link rel="icon" type="image/png" href="/static/logo.png">'
html += '<meta name="description" content="AI pre-earnings momentum scanner for tech stocks. Track scores, analyst ratings, PE targets, and implied moves before earnings reports.">'
html += '<meta property="og:title" content="AI Market Cap Scanner">'
html += '<meta property="og:description" content="Pre-earnings momentum scanner for AI/tech stocks. Scores, PE targets, 3-day and 5-day implied moves.">'
html += '<style>'"""

if old_head in content:
    content = content.replace(old_head, new_head)
    print('2. Meta tags added')
else:
    print('2. NOT found')

with open('ai_earnings_scanner.py', 'w', encoding='utf-8') as f:
    f.write(content)

import ast
try:
    ast.parse(content)
    print('Syntax OK!')
except SyntaxError as e:
    print(f'Syntax Error at line {e.lineno}: {e.msg}')