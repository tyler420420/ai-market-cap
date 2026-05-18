import yfinance as yf

tickers = ['INOD','NVDA','AMD','MSFT','GOOGL','META','AMZN','AVGO','TSM','CRM','ORCL','NOW','SNOW','PANW','CRWD','ZS','DDOG','PLTR','AI','U','SMCI','MRVL','INTC','QCOM','MU','TXN','LRCX','ASML','KLAC','AMAT','SNPS','CDNS','ADBE','TEAM','ADSK','INTU','CFLT','APP','VEEV','HPC','RAIN','GRAB']

from datetime import datetime, timedelta
today = datetime.now().date()
window_start = today + timedelta(days=5)
window_end = today + timedelta(days=7)

print(f"Today: {today}")
print(f"Window: {window_start} to {window_end}")
print()

in_window = []
for t in tickers:
    try:
        cal = yf.Ticker(t).calendar
        if cal and 'Earnings Date' in cal:
            ed = cal['Earnings Date']
            if isinstance(ed, list) and ed:
                edate = ed[0]
                if hasattr(edate, 'date'): edate = edate.date()
                days = (edate - today).days
                if window_start <= edate <= window_end:
                    in_window.append((t, edate, days))
    except: pass

if in_window:
    print(f"Found {len(in_window)} stocks in 5-7 day window:")
    for t, d, n in sorted(in_window, key=lambda x: x[2]):
        print(f"  {t}: {d} ({n} days)")
else:
    print("No stocks in exact 5-7 day window. Broadening to 4-10 days...")
    for t in tickers:
        try:
            cal = yf.Ticker(t).calendar
            if cal and 'Earnings Date' in cal:
                ed = cal['Earnings Date']
                if isinstance(ed, list) and ed:
                    edate = ed[0]
                    if hasattr(edate, 'date'): edate = edate.date()
                    days = (edate - today).days
                    if 4 <= days <= 10:
                        in_window.append((t, edate, days))
        except: pass
    in_window.sort(key=lambda x: x[2])
    for t, d, n in in_window:
        print(f"  {t}: {d} ({n} days)")