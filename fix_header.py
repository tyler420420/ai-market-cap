f=open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','r',encoding='utf-8')
c=f.read()
f.close()
# Update description text
c=c.replace('Pre-earnings momentum scanner for AI/AI-niche sector | Auto-runs daily at 6:30 AM PT | Subscribe to unlock Run Scan &amp; Chat','Pre-earnings momentum scanner for tech stocks | Auto-runs free daily at 6:30 AM PT | UPGRADE TO USE RUN SCAN AND CHAT')
# Add upgrade button after description
c=c.replace('</div></div><div style="display:flex;flex-direction:column;gap:8px;align-items:flex-end;margin-left:auto">','</div></div><div style="display:flex;flex-direction:column;gap:8px;align-items:flex-end;margin-left:auto"><button onclick="window.location.href=\'/pricing\'" style="background:#ffd700;color:#000;border:none;padding:8px 16px;border-radius:6px;font-size:0.85em;font-weight:bold;cursor:pointer">UPGRADE</button>')
f=open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html','w',encoding='utf-8')
f.write(c)
f.close()
print('done')