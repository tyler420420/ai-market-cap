with open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Strong Buy badge: "7" Watch should be "5"
html = html.replace(
    '<span style="font-weight:bold;color:#58a6ff">7</span> <span style="color:#8b949e">Watch</span>',
    '<span style="font-weight:bold;color:#58a6ff">5</span> <span style="color:#8b949e">Watch</span>'
)

# 2. Static HTML rows: remove bold from 3 Day column
import re
html = re.sub(
    r'<td data-label="3 Day"><span style="font-weight:bold">(\$[^<]+)</span><br>',
    r'<td data-label="3 Day">\1<br>',
    html
)

# 3. renderTable JS: remove bold from pe_target (3 Day column)
old_pe = "html+='<td><span style=\"font-weight:bold\">$'+Math.floor(r.pe_target)+'<br><span style=\"color:#00ff88\">+'+r.pe_upside+'%</span></td>';"
new_pe = "html+='<td>$'+Math.floor(r.pe_target)+' | +'+r.pe_upside+'%</td>';"
if old_pe in html:
    html = html.replace(old_pe, new_pe)
    print("Fixed renderTable 3 Day bold")
else:
    print("renderTable 3 Day pattern NOT found - checking...")
    # Try to find it
    idx = html.find("r.pe_target")
    if idx >= 0:
        print(repr(html[idx-100:idx+100]))

with open('C:\\Users\\Tyler_AI\\Desktop\\test_scanner.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Done. Strong Buy badge fixed.")
