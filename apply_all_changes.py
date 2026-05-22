with open('ai_earnings_scanner.py','r',encoding='utf-8') as f:
    lines = f.readlines()

# 1. viewport meta
lines[370] = "    html += '<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"><meta charset=\"UTF-8\"><title>' + SCANNER_TITLE + '</title>'\n"

# 2. btn CSS (line 377)
for i, line in enumerate(lines):
    if ".btn{background:#238636;border:none;color:#fff;padding:10px 22px" in line:
        lines[i] = line.replace(
            ".btn{background:#238636;border:none;color:#fff;padding:10px 22px;border-radius:6px;font-size:0.9em;cursor:pointer;font-weight:bold;flex-shrink:0}.btn:hover{background:#2ea043}.btn:disabled{background:#444;cursor:not-allowed}#refreshBtn{background:#1f6feb}#refreshBtn:hover{background:#388bfd}",
            ".btn{background:#ffd700;border:2px solid #000;color:#000;padding:10px 22px;border-radius:6px;font-size:0.9em;cursor:pointer;font-weight:bold;flex-shrink:0;box-shadow:0 0 12px rgba(255,215,0,0.5)}.btn:hover{background:#2ea043}.btn:active{background:#238636}.btn:disabled{background:#444;cursor:not-allowed}#refreshBtn{background:#1f6feb;border:2px solid #000;box-shadow:0 0 12px rgba(31,111,235,0.5)}#refreshBtn:hover{background:#388bfd}"
        )
        break

# 3. chat-btn CSS
for i, line in enumerate(lines):
    if "#chat-btn{position:fixed;bottom:24px;right:24px;background:#238636" in line:
        lines[i] = line.replace(
            "#chat-btn{position:fixed;bottom:24px;right:24px;background:#238636;color:#fff;border:none;border-radius:8px;padding:12px 24px;font-size:0.95em;font-weight:bold;cursor:pointer;box-shadow:0 4px 20px rgba(0,0,0,0.5);z-index:9999;transition:background .2s}",
            "#chat-btn{position:fixed;bottom:24px;right:24px;background:#ffd700;color:#000;border:2px solid #000;border-radius:10px;padding:14px 28px;font-size:1.05em;font-weight:bold;cursor:pointer;box-shadow:0 0 12px rgba(255,215,0,0.5);z-index:9999}"
        )
        break

# 4. chat-btn hover
for i, line in enumerate(lines):
    if "#chat-btn:hover{background:#2ea043}" in line:
        lines[i] = line.replace("#chat-btn:hover{background:#2ea043}", "#chat-btn:hover{background:#e6c200}")
        break

# 5. pick-banner inline style (near line 444)
for i, line in enumerate(lines):
    if "pick-banner style=\"background:linear-gradient" in line:
        lines[i] = line.replace(
            "background:linear-gradient(135deg,#2a1a00,#ffd700);border:2px solid #ffd700;border-radius:8px;padding:40px 18px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:15px 0;min-height:120px",
            "background:#161b22;border:2px solid #2ea043;border-radius:10px;padding:40px 18px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:15px 0;min-height:120px;box-shadow:0 0 20px rgba(46,160,67,0.4)"
        )
        break

# 6. header subscribe link (line 431)
for i, line in enumerate(lines):
    if "Subscribe to unlock Run Scan" in line and "html += " in lines[i-1]:
        lines[i] = line.replace(
            "Subscribe to unlock Run Scan & Chat",
            '<a href=\"/pricing\" style=\"color:#ffd700;text-decoration:underline\">Subscribe to unlock Run Scan &amp; Chat</a>'
        )
        break

# 7. column headers (line 458)
for i, line in enumerate(lines):
    if "Post Earnings<br>Target" in line:
        lines[i] = line.replace(
            "('Post Earnings<br>Target','pe_target'), ('Great Earnings Report','3 Day PE'), ('Excellent Earnings Report','5 Day PE'),",
            "('PE Target','pe_target'), ('3 Day','3 Day'), ('5 Day','5 Day'),"
        )
        break

# 8. earnings_date in rowsData - strip year
for i, line in enumerate(lines):
    if "'earnings_date': stock.earnings_date," in line and "stock.composite_score" in lines[i-1]:
        lines[i] = line.replace("'earnings_date': stock.earnings_date,", "'earnings_date': stock.earnings_date,")
        break

# 9. fmtEdate function in JS string (need to find inside the big html string)
# Find the line with scoreColor function
for i, line in enumerate(lines):
    if "function scoreColor(s){return s>=80?'#00ff88':'" in line:
        # This is the big JS string line - add fmtEdate after scoreColor
        old_sc = "function scoreColor(s){return s>=80?'#00ff88':'#58a6ff';}"
        new_sc = "function scoreColor(s){return s>=80?'#00ff88':'#58a6ff';}function fmtEdate(s){if(!s)return'';var p=s.split('-');var months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];var m=parseInt(p[1]);return months[m-1]+' '+p[2]+'\\n'+p[0];}"
        lines[i] = lines[i].replace(old_sc, new_sc)
        break

# 10. Change earnings_date cell in renderTable to use fmtEdate
for i, line in enumerate(lines):
    if "html+='<td>'+r.earnings_date+'</td>'" in line:
        lines[i] = line.replace(
            "html+='<td>'+r.earnings_date+'</td>'",
            "html+='<td style=\"font-size:0.85em\">'+fmtEdate(r.earnings_date)+'</td>'"
        )
        break

with open('ai_earnings_scanner.py','w',encoding='utf-8') as f:
    f.writelines(lines)
print('All changes applied')