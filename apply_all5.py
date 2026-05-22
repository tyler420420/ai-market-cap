# Read the file
with open('ai_earnings_scanner.py','r',encoding='utf-8') as f:
    content = f.read()

import re

# === FIX 1: viewport meta tag ===
content = content.replace(
    "html += '<meta charset=\"UTF-8\"><title>' + SCANNER_TITLE + '</title>'",
    "html += '<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"><meta charset=\"UTF-8\"><title>' + SCANNER_TITLE + '</title>'"
)

# === FIX 2: btn CSS ===
content = content.replace(
    ".btn{background:#238636;border:none;color:#fff;padding:10px 22px;border-radius:6px;font-size:0.9em;cursor:pointer;font-weight:bold;flex-shrink:0}.btn:hover{background:#2ea043}.btn:disabled{background:#444;cursor:not-allowed}#refreshBtn{background:#1f6feb}#refreshBtn:hover{background:#388bfd}",
    ".btn{background:#ffd700;border:2px solid #000;color:#000;padding:10px 22px;border-radius:6px;font-size:0.9em;cursor:pointer;font-weight:bold;flex-shrink:0;box-shadow:0 0 12px rgba(255,215,0,0.5)}.btn:hover{background:#2ea043}.btn:active{background:#238636}.btn:disabled{background:#444;cursor:not-allowed}#refreshBtn{background:#1f6feb;border:2px solid #000;box-shadow:0 0 12px rgba(31,111,235,0.5)}#refreshBtn:hover{background:#388bfd}"
)

# === FIX 3: chat-btn CSS ===
content = content.replace(
    "#chat-btn{position:fixed;bottom:24px;right:24px;background:#238636;color:#fff;border:none;border-radius:8px;padding:12px 24px;font-size:0.95em;font-weight:bold;cursor:pointer;box-shadow:0 4px 20px rgba(0,0,0,0.5);z-index:9999;transition:background .2s}",
    "#chat-btn{position:fixed;bottom:24px;right:24px;background:#ffd700;color:#000;border:2px solid #000;border-radius:10px;padding:14px 28px;font-size:1.05em;font-weight:bold;cursor:pointer;box-shadow:0 0 12px rgba(255,215,0,0.5);z-index:9999}"
)

# === FIX 4: chat-btn hover ===
content = content.replace("#chat-btn:hover{background:#2ea043}", "#chat-btn:hover{background:#e6c200}")

# === FIX 5: pick-banner inline style ===
content = content.replace(
    'background:linear-gradient(135deg,#2a1a00,#ffd700);border:2px solid #ffd700;border-radius:8px;padding:40px 18px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:15px 0;min-height:120px',
    'background:#161b22;border:2px solid #2ea043;border-radius:10px;padding:40px 18px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:15px 0;min-height:120px;box-shadow:0 0 20px rgba(46,160,67,0.4)'
)

# === FIX 6: header subscribe link ===
content = content.replace(
    "Subscribe to unlock Run Scan &amp; Chat</div>",
    '<a href="/pricing" style="color:#ffd700;text-decoration:underline" onmouseover="this.style.color=\\'#2ea043\\'" onmouseout="this.style.color=\\'#ffd700\\'">Subscribe to unlock Run Scan &amp; Chat</a></div>'
)

# === FIX 7: column headers ===
content = content.replace(
    "('Post Earnings<br>Target','pe_target'), ('Great Earnings Report','3 Day PE'), ('Excellent Earnings Report','5 Day PE'),",
    "('PE Target','pe_target'), ('3 Day','3 Day'), ('5 Day','5 Day'),"
)

# === FIX 8: earnings_date formatting in rowsData ===
# Format it as M-DD\nYYYY in Python before it goes to JS
content = content.replace(
    "'earnings_date': stock.earnings_date,",
    "'earnings_date': stock.earnings_date and stock.earnings_date[5:].replace('-', chr(45)) + chr(10) + stock.earnings_date[:4] or '',"
)

# === FIX 9: earnings_date cell in renderTable - just show r.earnings_date ===
content = content.replace(
    "html+='<td>'+r.earnings_date+'</td>'",
    "html+='<td style=\"font-size:0.85em\">'+r.earnings_date+'</td>'"
)

# Check syntax
try:
    compile(content, 'ai_earnings_scanner.py', 'exec')
    print('Syntax OK')
    with open('ai_earnings_scanner.py','w',encoding='utf-8') as f:
        f.write(content)
    print('Saved')
except SyntaxError as e:
    print('SyntaxError at line', e.lineno, 'offset', e.offset)
    lines = content.split('\n')
    print(repr(lines[e.lineno-1][e.offset-20:e.offset+20]))