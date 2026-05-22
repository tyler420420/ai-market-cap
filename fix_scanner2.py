content = open('ai_earnings_scanner.py', encoding='utf-8').read()

# Fix 1: Add meta tags and favicon after title
old = "<title>' + SCANNER_TITLE + '</title>'"
new = "<title>' + SCANNER_TITLE + '</title>' + \\\n        '<link rel=\"icon\" type=\"image/png\" href=\"/static/logo.png\">' + \\\n        '<meta name=\"description\" content=\"AI pre-earnings momentum scanner for tech stocks. Track scores, analyst ratings, PE targets, and implied moves before earnings reports.\">'"
if old in content:
    content = content.replace(old, new)
    print('1. Meta tags added')
else:
    print('1. NOT found')

# Fix 2: Add sticky bar at top
old2 = "html += '<div class=header><div class=hdr-row><div><h1>' + SCANNER_TITLE + '</h1>"
new2 = "html += '<div style=\"background:#1a2a1a;border-bottom:2px solid #2ea043;padding:10px 20px;text-align:center;font-size:0.9em\"><span style=\"color:#2ea043\">&#10003;</span> Free scan runs daily at 6:30 AM PT &nbsp;|&nbsp; <a href=\"/pricing\" style=\"color:#ffd700;font-weight:bold;text-decoration:none\">Subscribe to run additional scans</a> &nbsp;|&nbsp; <a href=\"/pricing\" style=\"color:#ffd700;text-decoration:none\">+ AI Trading Chat Assistant</a></div>' + \\\n        '<div class=header><div class=hdr-row><div><a href=\"https://aismarketcap.com\" style=\"color:#58a6ff;text-decoration:none\"><h1>' + SCANNER_TITLE + '</h1></a><div class=desc>Pre-earnings momentum scanner for Tech sector</div></div>'"
if old2 in content:
    content = content.replace(old2, new2)
    print('2. Sticky bar + title link added')
else:
    print('2. NOT found')

# Fix 3: Add How It Works button before Refresh
old3 = "<button class=btn id=refreshBtn onclick=refreshData()>Refresh</button>"
new3 = "<a href=\"/about\" class=\"btn\" style=\"background:#1a2a2a;border:1px solid #30363d;color:#58a6ff;padding:10px 18px;border-radius:6px;font-size:0.9em;text-decoration:none;font-weight:normal\">How It Works</a><button class=btn id=refreshBtn onclick=refreshData()>Refresh</button>"
if old3 in content:
    content = content.replace(old3, new3)
    print('3. How It Works button added')
else:
    print('3. NOT found')

# Fix 4: Change "Updated:" to "Last Updated:"
old4 = "'<div class=updated>Updated: ' + timestamp"
new4 = "'<div class=updated>Last Updated: ' + timestamp"
if old4 in content:
    content = content.replace(old4, new4)
    print('4. Timestamp label fixed')
else:
    print('4. NOT found')

with open('ai_earnings_scanner.py', 'w', encoding='utf-8') as f:
    f.write(content)

import ast
try:
    ast.parse(content)
    print('Syntax OK!')
except SyntaxError as e:
    print(f'Syntax Error at line {e.lineno}: {e.msg}')