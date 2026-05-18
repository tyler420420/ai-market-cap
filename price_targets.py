import yfinance as yf

for t, ed in [('DUOT','May 18'), ('ZS','May 26'), ('SNOW','May 27')]:
    s = yf.Ticker(t).info
    price = s.get('currentPrice', s.get('regularMarketPrice', 0))
    target = s.get('targetMeanPrice', 0)
    high = s.get('targetHighPrice', 0)
    low = s.get('targetLowPrice', 0)
    analysts = s.get('numberOfAnalystOpinions', 0)
    rec = s.get('recommendationKey','')
    upside = ((target - price) / price * 100) if price > 0 and target > 0 else 0
    print(f'{t} (Earnings: {ed})')
    print(f'  Current: ${price:.2f}')
    print(f'  Target:  ${target:.2f} ({upside:+.0f}%)')
    print(f'  Range:   ${low:.2f} - ${high:.2f}')
    print(f'  Analysts: {analysts} | Rec: {rec}')
    print()