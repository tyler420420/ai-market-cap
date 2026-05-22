with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. getVal - replace squeeze with sentiment
old1 = "'short_int':r.short_int,'iv':r.iv,'squeeze':r.squeeze"
new1 = "'short_int':r.short_int,'iv':r.iv,'sentiment':r.sentiment"
c = c.replace(old1, new1)
print('getVal:', old1 in open('ai_earnings_scanner.py').read() == False)

# 2. sortBy - remove squeeze, add sentiment
old2 = "col==='short_int'||col==='iv'||col==='squeeze';}"
new2 = "col==='short_int'||col==='iv'||col==='sentiment';}"
c = c.replace(old2, new2)

# 3. renderTable - replace squeeze cell with sentiment cell
old3 = "html+='<td>'+(r.squeeze?'<span style=\"background:#1a2a1a;border:1px solid #2ea043;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#00ff88\">Yes</span>':'—')+'</td>'"
new3 = "var sent=r.sentiment||'';var sentBg='';if(sent==='Positive')sentBg='background:#1a2a1a;border:1px solid #2ea043;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#00ff88';else if(sent==='Negative')sentBg='background:#2a1a1a;border:1px solid #ff4444;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#ff6b6b';else if(sent==='Mixed')sentBg='background:#2a2a1a;border:1px solid #ffd700;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#ffd700';html+='<td>'+(sent?'<span style=\"'+sentBg+'\">'+sent+'</span>':'—')+'</td>'"
c = c.replace(old3, new3)

with open('ai_earnings_scanner.py', 'w', encoding='utf-8') as f:
    f.write(c)
print('All done')