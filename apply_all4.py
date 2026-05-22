with open('ai_earnings_scanner.py','r',encoding='utf-8') as f:
    lines = f.readlines()

changes = 0

# 1. viewport
for i,l in enumerate(lines):
    if '<meta charset="UTF-8"><title>' in l and 'html +=' in l:
        lines[i] = l.replace('<meta charset="UTF-8"><title>','<meta name="viewport" content="width=device-width, initial-scale=1"><meta charset="UTF-8"><title>')
        changes += 1
        break

# 2. btn CSS
for i,l in enumerate(lines):
    if '.btn{background:#238636;border:none;color:#fff;padding:10px 22px' in l:
        lines[i] = l.replace(
            '.btn{background:#238636;border:none;color:#fff;padding:10px 22px;border-radius:6px;font-size:0.9em;cursor:pointer;font-weight:bold;flex-shrink:0}.btn:hover{background:#2ea043}.btn:disabled{background:#444;cursor:not-allowed}#refreshBtn{background:#1f6feb}#refreshBtn:hover{background:#388bfd}',
            '.btn{background:#ffd700;border:2px solid #000;color:#000;padding:10px 22px;border-radius:6px;font-size:0.9em;cursor:pointer;font-weight:bold;flex-shrink:0;box-shadow:0 0 12px rgba(255,215,0,0.5)}.btn:hover{background:#2ea043}.btn:active{background:#238636}.btn:disabled{background:#444;cursor:not-allowed}#refreshBtn{background:#1f6feb;border:2px solid #000;box-shadow:0 0 12px rgba(31,111,235,0.5)}#refreshBtn:hover{background:#388bfd}'
        )
        changes += 1
        break

# 3. chat-btn
for i,l in enumerate(lines):
    if '#chat-btn{position:fixed;bottom:24px;right:24px;background:#238636' in l:
        lines[i] = l.replace(
            '#chat-btn{position:fixed;bottom:24px;right:24px;background:#238636;color:#fff;border:none;border-radius:8px;padding:12px 24px;font-size:0.95em;font-weight:bold;cursor:pointer;box-shadow:0 4px 20px rgba(0,0,0,0.5);z-index:9999;transition:background .2s}',
            '#chat-btn{position:fixed;bottom:24px;right:24px;background:#ffd700;color:#000;border:2px solid #000;border-radius:10px;padding:14px 28px;font-size:1.05em;font-weight:bold;cursor:pointer;box-shadow:0 0 12px rgba(255,215,0,0.5);z-index:9999}'
        )
        changes += 1
        break

# 4. chat-btn hover
for i,l in enumerate(lines):
    if '#chat-btn:hover{background:#2ea043}' in l:
        lines[i] = l.replace('#chat-btn:hover{background:#2ea043}','#chat-btn:hover{background:#e6c200}')
        changes += 1
        break

# 5. pick-banner
for i,l in enumerate(lines):
    if 'pick-banner style="background:linear-gradient' in l:
        lines[i] = l.replace(
            'background:linear-gradient(135deg,#2a1a00,#ffd700);border:2px solid #ffd700;border-radius:8px;padding:40px 18px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:15px 0;min-height:120px',
            'background:#161b22;border:2px solid #2ea043;border-radius:10px;padding:40px 18px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:15px 0;min-height:120px;box-shadow:0 0 20px rgba(46,160,67,0.4)'
        )
        changes += 1
        break

# 6. subscribe link
for i,l in enumerate(lines):
    if 'Subscribe to unlock Run Scan &amp; Chat</div>' in l:
        lines[i] = l.replace(
            'Subscribe to unlock Run Scan &amp; Chat</div>',
            '<a href="/pricing" style="color:#ffd700;text-decoration:underline" onmouseover="this.style.color=\'#2ea043\'" onmouseout="this.style.color=\'#ffd700\'">Subscribe to unlock Run Scan &amp; Chat</a></div>'
        )
        changes += 1
        break

# 7. column headers
for i,l in enumerate(lines):
    if "('Post Earnings<br>Target','pe_target')" in l:
        lines[i] = l.replace(
            "('Post Earnings<br>Target','pe_target'), ('Great Earnings Report','3 Day PE'), ('Excellent Earnings Report','5 Day PE'),",
            "('PE Target','pe_target'), ('3 Day','3 Day'), ('5 Day','5 Day'),"
        )
        changes += 1
        break

# 8. fmtEdate in JS
br = chr(60)+chr(98)+chr(114)+chr(62)
fmtEdate = "function fmtEdate(s){if(!s)return'';var p=s.split('-');return parseInt(p[1])+'-'+p[2]+'"+br+"<sub>'+p[0]+'</sub>';}"
for i,l in enumerate(lines):
    if "function scoreColor(s){return s>=80?'#00ff88':'" in l:
        lines[i] = l.replace(
            "function scoreColor(s){return s>=80?'#00ff88':'#58a6ff';}",
            "function scoreColor(s){return s>=80?'#00ff88':'#58a6ff';"+fmtEdate+"}"
        )
        changes += 1
        break

# 9. earnings_date cell
for i,l in enumerate(lines):
    if "html+='<td>'+r.earnings_date+'</td>'" in l:
        lines[i] = l.replace(
            "html+='<td>'+r.earnings_date+'</td>'",
            "html+='<td style=\"font-size:0.85em\">'+fmtEdate(r.earnings_date)+'</td>'"
        )
        changes += 1
        break

with open('ai_earnings_scanner.py','w',encoding='utf-8') as f:
    f.writelines(lines)

print('Applied', changes, 'changes')
try:
    compile(open('ai_earnings_scanner.py','r',encoding='utf-8').read(),'x','exec')
    print('Syntax OK')
except SyntaxError as e:
    print('SyntaxError:', e)