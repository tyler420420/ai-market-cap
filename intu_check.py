import yfinance as yf
t = yf.Ticker('INTU')
info = t.info
cp = info.get('currentPrice', 393)
print(f"Current: ${cp}")
print(f"12M analyst target: ${round(info.get('targetMeanPrice',0),2)} (+{round((info.get('targetMeanPrice',0)/cp-1)*100,1)}%)")
opt = t.option_chain('2026-05-22')
calls = opt.calls.copy(); puts = opt.puts.copy()
calls['abs_ITM'] = abs(calls['strike'] - cp); puts['abs_ITM'] = abs(puts['strike'] - cp)
atm_c = calls.loc[calls['abs_ITM'].idxmin()]; atm_p = puts.loc[puts['abs_ITM'].idxmin()]
call_price = atm_c.get('lastPrice', 0) or atm_c.get('bid', 0)
put_price = atm_p.get('lastPrice', 0) or atm_p.get('ask', 0)
straddle = call_price + put_price
print(f"May 22 straddle: ${round(straddle,2)} ({atm_c.get('strike')}C at ${round(call_price,2)} + {atm_p.get('strike')}P at ${round(put_price,2)})")
print(f"1-week target: ${round(cp + straddle, 2)} | +{round(straddle/cp*100,1)}%")
print(f"Straddle x1.5: ${round(straddle*1.5,2)} | +{round(straddle*1.5/cp*100,1)}%")