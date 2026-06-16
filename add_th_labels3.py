path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_today.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = [
    ('onclick="sortBy(\'ticker\')" data-col="ticker">Ticker', 'onclick="sortBy(\'ticker\')" data-col="ticker" data-label="Ticker">Ticker'),
    ('onclick="sortBy(\'company_name\')" data-col="company_name">Company', 'onclick="sortBy(\'company_name\')" data-col="company_name" data-label="Company">Company'),
    ('onclick="sortBy(\'score\')" data-col="score">Overall', 'onclick="sortBy(\'score\')" data-col="score" data-label="Score">Overall'),
    ('onclick="sortBy(\'earnings_date\')" data-col="earnings_date">Earnings', 'onclick="sortBy(\'earnings_date\')" data-col="earnings_date" data-label="Earnings">Earnings'),
    ('onclick="sortBy(\'days_left\')" data-col="days_left">Days', 'onclick="sortBy(\'days_left\')" data-col="days_left" data-label="Days">Days'),
    ('onclick="sortBy(\'price\')" data-col="price">Current', 'onclick="sortBy(\'price\')" data-col="price" data-label="Price">Current'),
    ('onclick="sortBy(\'pe_target\')" data-col="pe_target">3 Day', 'onclick="sortBy(\'pe_target\')" data-col="pe_target" data-label="3 Day">3 Day'),
    ('onclick="sortBy(\'3d\')" data-col="3d">7 Day', 'onclick="sortBy(\'3d\')" data-col="3d" data-label="7 Day">7 Day'),
    ('onclick="sortBy(\'5d\')" data-col="5d">14 Day', 'onclick="sortBy(\'5d\')" data-col="5d" data-label="14 Day">14 Day'),
    ('onclick="sortBy(\'analysts\')" data-col="analysts">Total', 'onclick="sortBy(\'analysts\')" data-col="analysts" data-label="Analysts">Total'),
    ('onclick="sortBy(\'sb\')" data-col="sb">Strong', 'onclick="sortBy(\'sb\')" data-col="sb" data-label="Strong Buy">Strong'),
    ('onclick="sortBy(\'buy\')" data-col="buy">Buy', 'onclick="sortBy(\'buy\')" data-col="buy" data-label="Buy">Buy'),
    ('onclick="sortBy(\'hold\')" data-col="hold">Hold', 'onclick="sortBy(\'hold\')" data-col="hold" data-label="Hold">Hold'),
    ('onclick="sortBy(\'sell\')" data-col="sell">Sell', 'onclick="sortBy(\'sell\')" data-col="sell" data-label="Sell">Sell'),
    ('onclick="sortBy(\'mktcap\')" data-col="mktcap">Market', 'onclick="sortBy(\'mktcap\')" data-col="mktcap" data-label="Mkt Cap">Market'),
    ('onclick="sortBy(\'short_int\')" data-col="short_int">Total', 'onclick="sortBy(\'short_int\')" data-col="short_int" data-label="Shorts">Total'),
    ('onclick="sortBy(\'iv\')" data-col="iv">Implied', 'onclick="sortBy(\'iv\')" data-col="iv" data-label="IV">Implied'),
    ('onclick="sortBy(\'sentiment\')" data-col="sentiment">Earnings', 'onclick="sortBy(\'sentiment\')" data-col="sentiment" data-label="Trend">Earnings'),
    ('onclick="sortBy(\'news\')" data-col="news">Recent', 'onclick="sortBy(\'news\')" data-col="news" data-label="News">Recent'),
]

changes = 0
for old, new in replacements:
    if old in content:
        content = content.replace(old, new, 1)
        changes += 1

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'Done - {changes} th labels added')