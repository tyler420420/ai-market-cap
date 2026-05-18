import yfinance as yf

for t in ['CRM', 'ZS', 'SNOW']:
    s = yf.Ticker(t).info
    cal = yf.Ticker(t).calendar
    price = s.get('currentPrice', s.get('regularMarketPrice', 0))
    target = s.get('targetMeanPrice', 0)
    upside = ((target - price) / price * 100) if price > 0 and target > 0 else 0
    iv = 0
    try:
        opt = yf.Ticker(t).option_chain()
        if opt.calls.shape[0] > 0:
            atm = opt.calls[opt.calls['inTheMoney']==False]
            if len(atm)>0: iv = atm.iloc[0].get('impliedVolatility',0)*100
    except: pass
    si = (s.get('shortPercentOfFloat',0) or 0)*100
    rec = s.get('recommendationKey','')
    analysts = s.get('numberOfAnalystOpinions', 0)
    edate = cal.get('Earnings Date', ['N/A'])[0] if cal else 'N/A'
    if hasattr(edate, 'strftime'): edate = edate.strftime('%Y-%m-%d')
    print(f'{t}:')
    print(f'  Price: ${price:.2f} | Target: ${target:.2f} | Upside: {upside:.0f}%')
    print(f'  Earnings: {edate}')
    print(f'  IV: {iv:.0f}% | SI: {si:.1f}% | Analysts: {analysts}')
    print(f'  Rec: {rec}')
    print()