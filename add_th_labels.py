path = r'C:\Users\Tyler_AI\ai-market-cap\ai_earnings_today.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

th_replacements = [
    ('<th data-col="ticker">', '<th data-col="ticker" data-label="Ticker">'),
    ('<th data-col="company_name">', '<th data-col="company_name" data-label="Company">'),
    ('<th data-col="score">', '<th data-col="score" data-label="Score">'),
    ('<th class=earn-cell>', '<th class=earn-cell data-label="Earnings">'),
    ('<th data-col="days_left">', '<th data-col="days_left" data-label="Days">'),
    ('<th data-col="price">', '<th data-col="price" data-label="Price">'),
    ('<th data-col="pe_target">', '<th data-col="pe_target" data-label="3 Day">'),
    ('<th data-col="3d">', '<th data-col="3d" data-label="7 Day">'),
    ('<th data-col="5d">', '<th data-col="5d" data-label="14 Day">'),
    ('<th data-col="analysts">', '<th data-col="analysts" data-label="Analysts">'),
    ('<th data-col="sb">', '<th data-col="sb" data-label="Strong Buy">'),
    ('<th data-col="buy">', '<th data-col="buy" data-label="Buy">'),
    ('<th data-col="hold">', '<th data-col="hold" data-label="Hold">'),
    ('<th data-col="sell">', '<th data-col="sell" data-label="Sell">'),
    ('<th data-col="mktcap">', '<th data-col="mktcap" data-label="Mkt Cap">'),
    ('<th data-col="short_int">', '<th data-col="short_int" data-label="Shorts">'),
    ('<th data-col="iv">', '<th data-col="iv" data-label="IV">'),
    ('<th data-col="sentiment">', '<th data-col="sentiment" data-label="Trend">'),
    ('<th data-col="news">', '<th data-col="news" data-label="News">'),
]

changes = 0
for old, new in th_replacements:
    if old in content:
        content = content.replace(old, new, 1)
        changes += 1

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'Done - {changes} th labels added')