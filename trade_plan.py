import re
with open('C:/Users/Tyler_AI/.mavis/sessions/mvs_41a119d03ae849d59a2cdecd57e77d10/workspace/ai_earnings_57day_20260517_0104.html', 'r', encoding='utf-8') as f:
    html = f.read()

# AI's Suggested Trade banner
banner = re.search(r'<div class=pick-banner[^>]*>(.*?)</div>', html, re.DOTALL)
if banner:
    text = re.sub(r'<[^>]+>', ' ', banner.group(0))
    text = re.sub(r'\s+', ' ', text).strip()
    print('=== AI SUGGESTED TRADE ===')
    print(text[:400])
    print()

# Parse each row in the table
# Extract from strong buy rows (background:rgba(0,255,136...))
rows = re.findall(r'<tr style="background:rgba\(0,255,136[^"]*"(.*?)</tr>', html, re.DOTALL)
if not rows:
    # Try alternate pattern for strong buy
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL)

print('=== FULL SCAN - THIS WEEK ===')
print(f"{'#':2s} {'Ticker':6s} {'Score':5s} {'Days':4s} {'Price':8s} {'Target':8s} {'3D Mom':8s} {'5D Mom':8s} {'2K P&L':10s}")
print('-' * 80)

row_count = 0
for row in rows[1:11]:  # skip header
    row_count += 1
    t = re.search(r'<strong><a[^>]*>([A-Z]+)</a>', row)
    if not t:
        continue
    ticker = t.group(1)

    # Score cell (4th td)
    s_cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
    if len(s_cells) < 8:
        continue

    # Index 3 = Score
    score_m = re.search(r'<strong[^>]*>([0-9]+)</strong>', s_cells[3])
    score = int(score_m.group(1)) if score_m else 0

    # Days (index 5)
    days_m = re.search(r'([0-9]+)d', s_cells[5])
    days = days_m.group(1) if days_m else '?'

    # Price (index 6)
    price_m = re.search(r'\$?([0-9.]+)', s_cells[6])
    price = float(price_m.group(1)) if price_m else 0

    # PE Target (index 7)
    target_m = re.search(r'\$([0-9.]+)', s_cells[7])
    target = float(target_m.group(1)) if target_m else 0

    # 3D Mom (index 8)
    mom3 = s_cells[8].strip() if len(s_cells) > 8 else '?'

    # 5D Mom (index 9)
    mom5 = s_cells[9].strip() if len(s_cells) > 9 else '?'

    if price > 0:
        pnl = round((target - price) * 2000 / price, 2)
        color = 'BUY' if score >= 80 else 'WATCH'
        print(str(row_count).rjust(2) + "  " + ticker.rjust(6) + " " + str(score).rjust(5) + "   " + str(days).ljust(4) + "d $" + f"{price:.2f}".rjust(7) + " $" + f"{target:.2f}".rjust(7) + " " + mom3.ljust(8) + " " + mom5.ljust(8) + " +$" + f"{pnl:.2f}".rjust(8))

print()
print('KEY: Score 80+ = BUY | Score <80 = WATCH')
print('Strategy: Enter 1-14 days before earnings, Sell 1-5 days after beat')
print('3D Mom = Conservative target | 5D Mom = Maximum upside')