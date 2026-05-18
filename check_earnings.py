import yfinance as yf

for ticker in ['CRM', 'TEAM']:
    stock = yf.Ticker(ticker)
    info = stock.info
    earnings_date = info.get('earningsDate', info.get('earnings_dates', 'N/A'))
    next_earnings = info.get('earningsDate', None)
    print(f'{ticker}: {next_earnings}')