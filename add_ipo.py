c = open('ai_earnings_scanner.py', encoding='utf-8').read()

# Add IPO ticker div after stats-bar
old1 = "html += '<div class=stats-bar><div class=legend><span><span class=dot style=background:#00ff88></span> Score 80+: Strong Buy</span><span><span class=dot style=background:#58a6ff></span> Score &lt;80: Watch</span></div></div>'"
new1 = """html += '<div class=stats-bar><div class=legend><span><span class=dot style=background:#00ff88></span> Score 80+: Strong Buy</span><span><span class=dot style=background:#58a6ff></span> Score &lt;80: Watch</span></div></div>'
    html += '<div id=ipo-ticker style=\"background:#0d1520;border:1px solid #30363d;border-radius:8px;padding:10px 18px;margin:15px 0;font-size:0.85em;text-align:center\"><span style=\"color:#ffd700;font-weight:bold\">&#128293; IPO Watch:</span> <span id=ipo-name style=\"color:#58a6ff;font-weight:bold\"></span> <span id=ipo-detail style=\"color:#8b949e\"></span></div>'"""

if old1 in c:
    c = c.replace(old1, new1)
    print('1. IPO ticker div added')
else:
    print('1. NOT found')

# Add JS rotation before sortBy function
old2 = "function sortBy(col){"
new2 = """var ipos=[{name:'SpaceX',detail:'Aerospace | $1.5T val | Late 2026'},{name:'OpenAI',detail:'AI | $1T val | 2026-2027'},{name:'Anthropic',detail:'AI | $300B val | Late 2026'},{name:'Databricks',detail:'Data/AI | $134B val | Q3 2026'},{name:'Stripe',detail:'Fintech | $159B val | TBD'},{name:'Canva',detail:'Design | $42B val | Q3 2026'},{name:'Kraken',detail:'Crypto | $20B val | Q3 2026'},{name:'Revolut',detail:'Fintech | $75B val | Q4 2026'},{name:'Monzo',detail:'Fintech | $8B val | Q2 2026'},{name:'Discord',detail:'Social | $15B val | Q2 2026'}];var ipoIdx=0;function rotateIpo(){var i=ipos[ipoIdx%ipos.length];document.getElementById('ipo-name').textContent=i.name;document.getElementById('ipo-detail').textContent=i.detail;ipoIdx++};if(document.getElementById('ipo-name')){rotateIpo();setInterval(rotateIpo,5000)}

function sortBy(col){"""

if old2 in c:
    c = c.replace(old2, new2)
    print('2. IPO JS rotation added')
else:
    print('2. NOT found')

open('ai_earnings_scanner.py', 'w', encoding='utf-8').write(c)

import ast
try:
    ast.parse(c)
    print('Syntax OK')
except SyntaxError as e:
    print(f'Syntax Error at line {e.lineno}')