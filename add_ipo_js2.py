c = open('ai_earnings_scanner.py', encoding='utf-8').read()

# Add IPO JS before the big script line
old = "html += '<script>var rowsData=' + json.dumps(rows_data) + ';\n'"
new = """html += \"<script>var rowsData=' + json.dumps(rows_data) + ';'\"
    html += \"var ipos=[{name:'SpaceX',detail:'Aerospace | $1.5T | Late 2026'},{name:'OpenAI',detail:'AI | $1T | 2026-2027'},{name:'Anthropic',detail:'AI | $300B | Late 2026'},{name:'Databricks',detail:'Data/AI | $134B | Q3 2026'},{name:'Stripe',detail:'Fintech | $159B | TBD'},{name:'Canva',detail:'Design | $42B | Q3 2026'},{name:'Kraken',detail:'Crypto | $20B | Q3 2026'},{name:'Revolut',detail:'Fintech | $75B | Q4 2026'},{name:'Monzo',detail:'Fintech | $8B | Q2 2026'},{name:'Discord',detail:'Social | $15B | Q2 2026'}];\"
    html += \"var ipoIdx=0;function rotateIpo(){var i=ipos[ipoIdx%ipos.length];document.getElementById('ipo-name').textContent=i.name;document.getElementById('ipo-detail').textContent=i.detail;ipoIdx++};if(document.getElementById('ipo-name')){rotateIpo();setInterval(rotateIpo,5000)}\"
    html += '<script>var rowsData=' + json.dumps(rows_data) + ';'\""""

if old in c:
    c = c.replace(old, new)
    open('ai_earnings_scanner.py', 'w', encoding='utf-8').write(c)
    print('JS added')
else:
    print('NOT found')