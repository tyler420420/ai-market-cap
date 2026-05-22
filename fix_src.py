# Fix ai_earnings_scanner.py - apply all local HTML changes to source

content = open('ai_earnings_scanner.py', encoding='utf-8').read()
changes = 0

# Fix 1: Add meta/OG/favicon tags after title
old1 = "html = '<!DOCTYPE html><html><head><meta charset=\"UTF-8\"><title>' + SCANNER_TITLE + '</title>'"
new1 = "html = '<!DOCTYPE html><html><head><meta charset=\"UTF-8\"><title>' + SCANNER_TITLE + '</title>'\n    html += '<link rel=\"icon\" type=\"image/png\" href=\"/static/logo.png\">'\n    html += '<meta name=\"description\" content=\"AI pre-earnings momentum scanner for tech stocks. Track scores, analyst ratings, PE targets, and implied moves before earnings reports.\">'\n    html += '<meta property=\"og:title\" content=\"AI Market Cap Scanner\">'\n    html += '<meta property=\"og:description\" content=\"Pre-earnings momentum scanner for AI/tech stocks. Scores, PE targets, 3-day and 5-day implied moves.\">'"
if old1 in content:
    content = content.replace(old1, new1)
    changes += 1
    print('1. Meta/OG/favicon tags added')
else:
    print('1. NOT found')

# Fix 2: Add sticky info bar before ticker strip
old2 = "html += '<div class=ticker-strip><div class=ticker-strip-inner>' + ticker_items + ticker_items + '</div></div>'"
new2 = "html += '<div style=\"background:#1a2a1a;border-bottom:2px solid #2ea043;padding:10px 20px;text-align:center;font-size:0.9em\"><span style=\"color:#2ea043\">&#10003;</span> Free scan runs daily at 6:30 AM PT &nbsp;|&nbsp; <a href=\"/pricing\" style=\"color:#ffd700;font-weight:bold;text-decoration:none\">Subscribe to run additional scans</a> &nbsp;|&nbsp; <a href=\"/pricing\" style=\"color:#ffd700;text-decoration:none\">+ AI Trading Chat Assistant</a></div>'\n    html += '<div class=ticker-strip><div class=ticker-strip-inner>' + ticker_items + ticker_items + '</div></div>'"
if old2 in content:
    content = content.replace(old2, new2)
    changes += 1
    print('2. Sticky bar added')
else:
    print('2. NOT found')

# Fix 3: Fix header - title link, desc, How It Works button, "Last Updated:"
old3 = "html += '<div class=header><div class=hdr-row><div><h1>' + SCANNER_TITLE + '</h1><div class=desc>Pre-earnings momentum scanner for Tech sector | Auto-runs daily at 6:30 AM PT | Subscribe to unlock Run Scan & Chat</div></div>'"
new3 = "html += '<div class=header><div class=hdr-row><div><a href=\"https://aismarketcap.com\" style=\"color:#58a6ff;text-decoration:none\"><h1>' + SCANNER_TITLE + '</h1></a><div class=desc>Pre-earnings momentum scanner for Tech sector</div></div>'"
if old3 in content:
    content = content.replace(old3, new3)
    changes += 1
    print('3a. Title link + desc fixed')
else:
    print('3a. NOT found')

# Fix 3b: Add How It Works button before Refresh
old3b = "html += '<button class=btn id=refreshBtn onclick=refreshData()>Refresh</button>'"
new3b = "html += '<a href=\"/about\" class=btn style=\"background:#1a2a2a;border:1px solid #30363d;color:#fff;padding:10px 18px;border-radius:6px;font-size:0.9em;text-decoration:none;font-weight:normal;box-shadow:none\">How It Works</a>'\n    html += '<button class=btn id=refreshBtn onclick=refreshData()>Refresh</button>'"
if old3b in content:
    content = content.replace(old3b, new3b)
    changes += 1
    print('3b. How It Works button added')
else:
    print('3b. NOT found')

# Fix 4: Change "Updated:" to "Last Updated:" and use human-readable timestamp
old4 = "timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')"
new4 = "timestamp = datetime.now().strftime('%B %d, %Y at %I:%M %p PT')"
if old4 in content:
    content = content.replace(old4, new4)
    changes += 1
    print('4. Human-readable timestamp')
else:
    print('4. NOT found')

# Fix 5: Fix updated div - no more data source attribution
old5 = "html += '<div class=updated>Updated: ' + timestamp + ' | Price data from Yahoo Finance | Options data via Yahoo Finance</div>'"
new5 = "html += '<div class=updated>Last Updated: ' + timestamp + '</div>'"
if old5 in content:
    content = content.replace(old5, new5)
    changes += 1
    print('5. Updated div fixed')
else:
    print('5. NOT found')

with open('ai_earnings_scanner.py', 'w', encoding='utf-8') as f:
    f.write(content)

import ast
try:
    ast.parse(content)
    print(f'\nAll {changes} changes applied. Syntax OK.')
except SyntaxError as e:
    print(f'Syntax Error at line {e.lineno}: {e.msg}')