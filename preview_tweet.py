import sys
sys.path.insert(0, 'C:/Users/Tyler_AI/ai-market-cap')
from x_poster import fetch_scanner_data

stocks = fetch_scanner_data()
if not stocks:
    print("No stocks fetched")
    sys.exit()

strong = [s for s in stocks if s.get('score', 0) >= 75]
top5 = sorted(strong, key=lambda x: -x.get('days_left', 0))[:5]

print("Daily Top Strong Buy Targets - https://aismarketcap.com")
print()
for i, s in enumerate(top5, 1):
    ticker = s.get('ticker', '?')
    score = s.get('score', 0)
    price = round(s.get('price', 0))
    target = round(s.get('5d', 0))
    upside = round(s.get('5d_up', 0))
    print(f"{i}. {ticker} | ${price} -> ${target} (+{upside}%)")
print()
print("#StockMarket #OptionsTrading #DayTrading #Investing #AIStocks")