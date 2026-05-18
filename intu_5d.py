import yfinance as yf
t = yf.Ticker('INTU')
info = t.info
cp = 393
print(f"Current: ${cp}")
# May 22 straddle
opt = t.option_chain('2026-05-22')
calls = opt.calls.copy(); puts = opt.puts.copy()
calls['abs_ITM'] = abs(calls['strike'] - cp); puts['abs_ITM'] = abs(puts['strike'] - cp)
atm_c = calls.loc[calls['abs_ITM'].idxmin()]; atm_p = puts.loc[puts['abs_ITM'].idxmin()]
call_price = atm_c.get('lastPrice', 0) or atm_c.get('bid', 0)
put_price = atm_p.get('lastPrice', 0) or atm_p.get('ask', 0)
straddle_7d = call_price + put_price
straddle_5d = straddle_7d * (5/7)
print(f"May 22 straddle (7d): ${round(straddle_7d,2)} (ATM {atm_c.get('strike')})")
print(f"5-day straddle estimate: ${round(straddle_5d,2)} | +{round(straddle_5d/cp*100,1)}%")
print(f"5-day target: ${round(cp + straddle_5d, 2)} | +{round(straddle_5d/cp*100,1)}%")
# Jun 5 for comparison
opt2 = t.option_chain('2026-06-05')
calls2 = opt2.calls.copy(); puts2 = opt2.puts.copy()
calls2['abs_ITM'] = abs(calls2['strike'] - cp); puts2['abs_ITM'] = abs(puts2['strike'] - cp)
atm_c2 = calls2.loc[calls2['abs_ITM'].idxmin()]; atm_p2 = puts2.loc[puts2['abs_ITM'].idxmin()]
call2 = atm_c2.get('lastPrice', 0) or atm_c2.get('bid', 0)
put2 = atm_p2.get('lastPrice', 0) or atm_p2.get('ask', 0)
straddle_21d = call2 + put2
print(f"\nJune 5 straddle (21d): ${round(straddle_21d,2)} (ATM {atm_c2.get('strike')})")
print(f"21-day target: ${round(cp + straddle_21d, 2)} | +{round(straddle_21d/cp*100,1)}%")