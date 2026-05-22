import yfinance as yf

tickers = ['SNOW', 'ZS', 'CRM', 'MRVL', 'SMTC', 'NTAP', 'IOT', 'DELL', 'PANW', 'CRWD']
for t in tickers:
    try:
        ticker = yf.Ticker(t)
        info = ticker.info

        # Use recommendations_historical or earnings_history
        rec = ticker.earnings_history
        if rec is not None and len(rec) > 0:
            print(f"\n{t}: {len(rec)} earnings records")
            print(rec.head(3))
        else:
            # Try quarterly earnings
            q = ticker.quarterly_earnings
            if q is not None and len(q) > 0:
                print(f"\n{t} quarterly_earnings:")
                print(q.head(3))
            else:
                print(f"{t}: no earnings data")
    except Exception as e:
        print(f"{t}: ERROR - {e}")