import re

with open('ai_earnings_scanner.py', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Add squeeze to rows_data dict
old1 = "            'short_int': round(stock.short_interest, 1) if stock.short_interest else 0,\n            'iv': round(stock.implied_volatility, 1) if stock.implied_volatility else 0,"
new1 = """            'short_int': round(stock.short_interest, 1) if stock.short_interest else 0,
            'iv': round(stock.implied_volatility, 1) if stock.implied_volatility else 0,
            'squeeze': 1 if (stock.short_interest and stock.short_interest > 10 and stock.days_to_earnings <= 10) else 0,"""
if old1 in c:
    c = c.replace(old1, new1)
    print('Step 1 done: squeeze added to rows_data')
else:
    print('Step 1 FAILED: pattern not found')

# 2. Add Squeeze header
old2 = "        ('Short %','short_int'), ('IV','iv'), ('News','news')"
new2 = "        ('Short %','short_int'), ('IV','iv'), ('Squeeze','squeeze'), ('News','news')"
if old2 in c:
    c = c.replace(old2, new2)
    print('Step 2 done: Squeeze header added')
else:
    print('Step 2 FAILED: pattern not found')

# 3. Add squeeze cell in static rows
old3 = "        static_rows += '<td style=\"color:#fff\">' + str(r['short_int']) + '%</td>'\n        static_rows += '<td style=\"color:#fff\">' + str(r['iv']) + '%</td>'"
new3 = """        static_rows += '<td style="color:#fff">' + str(r['short_int']) + '%</td>'
        static_rows += '<td style="color:#fff">' + str(r['iv']) + '%</td>'
        sq_badge = '<span style="background:#1a0a0a;border:1px solid #ff4444;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#ff6b6b">SQUEEZE</span>' if r['squeeze'] else '—'
        static_rows += '<td>' + sq_badge + '</td>'"""
if old3 in c:
    c = c.replace(old3, new3)
    print('Step 3 done: squeeze cell added to static rows')
else:
    print('Step 3 FAILED: pattern not found')

with open('ai_earnings_scanner.py', 'w', encoding='utf-8') as f:
    f.write(c)
print('File saved')