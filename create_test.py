# Extract just the renderTable section and save as a standalone test
with open('ai_earnings_57day_20260519_2312.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Find where the big script ends
script_end = c.find('</script>')
script_start = c.find('<script>') + 8
script = c[script_start:script_end]

# Save it as a JS file
with open('test_render.js', 'w', encoding='utf-8') as f:
    f.write(script)

print(f'Script extracted: {len(script)} chars')
print('Saved to test_render.js')

# Now let's create a minimal HTML test
# Replace the massive script with just the renderTable function + call
mini_script = """
var rowsData=[{"rank":1,"ticker":"NVDA","score":99,"earnings_date":"2026-05-20","days_left":1,"price":220.61,"pe_target":234.17,"pe_upside":6.1,"3d":261.29,"3d_up":18.4,"5d":288.41,"5d_up":30.7,"analysts":57,"sb":10,"buy":48,"hold":2,"sell":1,"mktcap":5343.29,"news":null}];
function scoreColor(s){return s>=80?'#00ff88':'#58a6ff';}
function newsHtml(n){if(!n)return'';var u=n.url||'';var t=n.title||'';return u?'<a href="'+u+'" target="_blank" style="color:#fff;text-decoration:none">&#128240; '+t+'</a>':'<span style="color:#fff">&#128240; '+t+'</span>';}
function renderTable(){var tbody=document.getElementById('stockTableBody');if(!tbody){console.log('tbody not found!');return;}var html='';rowsData.forEach(function(r){var c=scoreColor(r.score);var bg=r.score>=80?'rgba(0,255,136,0.12)':'rgba(31,111,235,0.12)';html+='<tr style="background:'+bg+'"><td><strong>'+r.ticker+'</strong></td>';html+='<td>'+r.score+'</td></tr>';});tbody.innerHTML=html;}
renderTable();
"""

with open('test_mini.html', 'w', encoding='utf-8') as f:
    f.write("""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Mini Test</title></head>
<body>
<table id="stockTable"><thead><tr><th>Ticker</th><th>Score</th></tr></thead>
<tbody id="stockTableBody"></tbody></table>
<script>""" + mini_script + """</script>
</body></html>""")

print(f'Mini HTML created: {len(mini_script)} chars in script')