import yfinance as yf
import traceback

tickers = ['SNOW', 'ZS', 'CRM', 'MRVL', 'SMTC', 'NTAP', 'IOT', 'DELL', 'PANW', 'CRWD']
for t in tickers:
    try:
        ticker = yf.Ticker(t)
        info = ticker.info

        # Analyst sentiment
        buy_pct = info.get('buyPercent', 0) or 0

        # Recent earnings surprise
        try:
            eh = ticker.earnings_history
            if eh is not None and len(eh) > 0:
                last = eh.iloc[0]
                surprise = last.get('EPS Surprise', None)
                actual = last.get('EPS Actual', None)
                estimate = last.get('EPS Estimate', None)
                surprise_pct = last.get('Surprise %', 0) or 0
            else:
                surprise = None
                surprise_pct = 0
        except:
            surprise = None
            surprise_pct = 0

        # Earnings estimate for upcoming quarter
        try:
            ee = ticker.earnings_estimate
            if ee is not None and len(ee) > 0:
                next_q = ee[ee.index.get_level_values('period') == '0q'] if 'period' in ee.index.names else None
                if next_q is not None and len(next_q) > 0:
                    avg_est = next_q['avg'].iloc[0] if 'avg' in next_q.columns else None
                else:
                    avg_est = None
            else:
                avg_est = None
        except:
            avg_est = None

        verdict = 'Positive' if surprise_pct > 0 else ('Negative' if surprise_pct < 0 else 'Uncertain')
        print(f"{t}: Buy%={buy_pct:.0f}% | Surprise%={surprise_pct:.1f}% | EPS Est=${avg_est if avg_est else '?'} | {verdict}")
    except Exception as e:
        print(f"{t}: ERROR - {e}")