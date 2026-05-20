import yfinance as yf

tickers = ['DUOT', 'ZS', 'SNOW']
from datetime import datetime

for t in tickers:
    try:
        cal = yf.Ticker(t).calendar
        info = yf.Ticker(t).info
        price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        target = info.get('targetMeanPrice', 0)
        upside = ((target - price) / price * 100) if price > 0 and target > 0 else 0
        name = info.get('longName', info.get('shortName', t))
        sector = info.get('sector', 'N/A')
        if cal and 'Earnings Date' in cal:
            ed = cal['Earnings Date']
            if isinstance(ed, list) and ed:
                edate = ed[0]
                if hasattr(edate, 'date'): edate = edate.date()
                today = datetime.now().date()
                days = (edate - today).days
                print(f'{t} ({name})')
                print(f'  Sector: {sector}')
                print(f'  Price: ${price:.2f} | Target: ${target:.2f} | Upside: {upside:.0f}%')
                print(f'  Earnings: {edate} ({days} days from today)')
                print()
        else:
            print(f'{t}: No earnings data found')
    except Exception as e:
        print(f'{t}: Error - {e}')