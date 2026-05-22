c = open('ai_earnings_scanner.py', encoding='utf-8').read()

old = "function sortBy(col){"
new = """var ipos=[{name:'SpaceX',detail:'Aerospace | Est. $1.5T val | Late 2026'},{name:'OpenAI',detail:'AI | Est. $1T val | 2026-2027'},{name:'Anthropic',detail:'AI | Est. $300B val | Late 2026'},{name:'Databricks',detail:'Data/AI | Est. $134B val | Q3 2026'},{name:'Stripe',detail:'Fintech | Est. $159B val | TBD'},{name:'Canva',detail:'Design | Est. $42B val | Q3 2026'},{name:'Kraken',detail:'Crypto | Est. $20B val | Q3 2026'},{name:'Revolut',detail:'Fintech | Est. $75B val | Q4 2026'},{name:'Monzo',detail:'Fintech | Est. $8B val | Q2 2026'},{name:'Discord',detail:'Social | Est. $15B val | Q2 2026'}];var ipoIdx=0;function rotateIpo(){var i=ipos[ipoIdx%ipos.length];document.getElementById('ipo-name').textContent=i.name;document.getElementById('ipo-detail').textContent=i.detail;ipoIdx++};if(document.getElementById('ipo-name')){rotateIpo();setInterval(rotateIpo,5000)}

function sortBy(col){"""

if old in c:
    c = c.replace(old, new)
    open('ai_earnings_scanner.py', 'w', encoding='utf-8').write(c)
    print('Done')
else:
    print('NOT found')