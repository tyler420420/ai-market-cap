"""AI Earnings Scanner - Pre-Earnings Momentum Strategy (1-14 day window)"""
import argparse, csv, os, sys, time
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Optional

try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False


def fetch_ai_stocks_from_finviz() -> List[str]:
    """Fetch tech sector stocks dollar10B+ from finviz (cap_large + cap_mega)."""
    try:
        import requests
        from bs4 import BeautifulSoup
        tickers = set()
        for f in ['sec_technology,cap_large', 'sec_technology,cap_mega']:
            for page_start in range(1, 1001, 20):
                url = f"https://finviz.com/screener.ashx?v=152&f={f}&o=ticker&r={page_start}"
                resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}, timeout=15)
                soup = BeautifulSoup(resp.text, 'html.parser')
                table = soup.find('table', class_='screener_table')
                if not table: break
                rows = table.find_all('tr')[1:]
                if not rows: break
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        t = cells[1].get_text(strip=True)
                        if t.isalpha() and 1 <= len(t) <= 5: tickers.add(t)
                if len(rows) < 20: break
        result = sorted(tickers)
        print(f"[AI Stocks] Fetched {len(result)} tech stocks (dollar10B+) from finviz")
        return result
    except Exception as e:
        print(f"[AI Stocks] Finviz fetch failed: {e}. Using cached list.")
        return AI_TICKERS






def fetch_top_news(ticker: str, count: int = 1) -> List[dict]:
    """Get the top N recent news headlines for a ticker, filtered to relevant ones."""
    headlines = []
    try:
        ticker_obj = yf.Ticker(ticker)
        # Get company name for broader matching
        info = ticker_obj.info
        company_names = [ticker.upper()]
        for name_field in ['shortName', 'longName', 'name']:
            n = info.get(name_field, '') or ''
            if n and len(n) > 2:
                company_names.append(n.upper())
        news = ticker_obj.news
        if news:
            for item in news[:10]:
                title = item.get('title', '') or (item.get('content') or {}).get('title', '') or ''
                url = item.get('link', '') or item.get('url', '') or ''
                if not url:
                    content = item.get('content') or {}
                    ct = content.get('clickThroughUrl') or {}
                    url = (ct.get('url') if isinstance(ct, dict) else '') or ''
                if not url:
                    content = item.get('content') or {}
                    cu = content.get('canonicalUrl') or {}
                    url = (cu.get('url') if isinstance(cu, dict) else '') or ''
                if title and len(title) > 20:
                    title_clean = title.replace('&amp;', '&').replace('&quot;', '"').strip()
                    # Check if ticker or any company name appears in title
                    title_upper = title_clean.upper()
                    matched = ticker.upper() in title_upper
                    if not matched:
                        for cn in company_names:
                            # Match first significant word of company name (skip common words like CORP/LTD/INC)
                            parts = cn.split()
                            for part in parts:
                                if len(part) >= 4 and part not in ('CORP', 'CORPORATION', 'INC', 'LTD', 'LLC', 'PLC', 'THE', 'AND', 'OF'):
                                    import re
                                    if re.search(r'\b' + re.escape(part) + r'\b', title_upper):
                                        matched = True
                                        break
                            if matched:
                                break
                    if matched:
                        if len(title_clean) > 100:
                            title_clean = title_clean[:97] + '...'
                        headlines.append({'title': title_clean, 'url': url})
                        if len(headlines) >= count:
                            break
    except Exception:
        pass
    return headlines
# AI Infrastructure
AI_TICKERS = [
    'NVDA', 'AMD', 'AVGO', 'MRVL', 'INTC', 'QCOM', 'MU', 'TXN', 'LRCX', 'ASML', 'KLAC', 'AMAT', 'SNPS', 'CDNS',
    # AI Cloud/Enterprise
    'MSFT', 'GOOGL', 'AMZN', 'ORCL', 'NOW', 'SNOW', 'CRM',
    # AI Cybersecurity
    'PANW', 'CRWD', 'ZS',
    # AI Data/Analytics / Niche AI plays
    'INOD', 'DDOG', 'PLTR', 'AI', 'U', 'HPC', 'RAIN', 'GRAB',
    # Additional AI-niche
    'INTU', 'ADBE', 'TEAM', 'ADSK', 'CFLT', 'APP', 'VEEV', 'PATH',
    # EV/Solar AI plays
    'ENPH', 'SEDG', 'JKS', 'FSLR',
    # AI Healthcare/Biotech
    'MRNA', 'BILL',
    # AI Media/Other
    'UAA', 'LYFT', 'DOCU',
]

# Permanently excluded tickers (failed / high risk -- do not scan)
EXCLUDED_TICKERS = ['DUOT']


@dataclass
class EarningsSignal:
    ticker: str; company_name: str; earnings_date: str; days_to_earnings: int
    current_price: float; price_target: float; target_upside_pct: float
    post_earnings_target: float; post_earnings_upside_pct: float
    post_earnings_3d_target: float = 0.0; post_earnings_3d_upside_pct: float = 0.0
    post_earnings_5d_target: float = 0.0; post_earnings_5d_upside_pct: float = 0.0
    implied_volatility: float = 0.0
    strong_buy_rating: int = 0; buy_rating: int = 0; hold_rating: int = 0; sell_rating: int = 0; total_analysts: int = 0; buy_rating_pct: float = 0.0
    short_interest: float = 0.0; avg_volume: int = 0; sector: str = 'Technology'; market_cap: float = 0.0
    composite_score: float = 0.0; signals: List[str] = None
    top_news: List[str] = None; price_change_pct: float = 0.0; price_change_abs: float = 0.0
    def __post_init__(self):
        if self.signals is None: self.signals = []
        if self.top_news is None: self.top_news = []


def calculate_composite_score(stock: EarningsSignal) -> float:
    score = 0.0; signals = []

    # === 1. ANALYST COVERAGE (PRIMARY -- institutional validation = safety) ===
    if stock.total_analysts == 0:
        signals.append('WARNING: No analyst coverage (high risk, avoid)')
        score += 5
    elif stock.total_analysts < 10:
        signals.append(f'Thin coverage: {stock.total_analysts} analysts')
        score += 15
    elif stock.total_analysts >= 20:
        score += 30
        signals.append(f'{stock.total_analysts} analysts (institutional backing)')
    elif stock.total_analysts >= 10:
        score += 20
        signals.append(f'{stock.total_analysts} analysts')

    # === 2. BUY% (analyst conviction) ===
    if stock.buy_rating_pct > 0:
        buy_score = (stock.buy_rating_pct / 100) * 30; score += buy_score
        if stock.buy_rating_pct >= 80:
            signals.append(f'{stock.buy_rating_pct:.0f}% bullish ({stock.strong_buy_rating} SB + {stock.buy_rating} B)')

    # === 3. 5D UPSIDE (options-implied move, bonus -- more sensitive in 5-15% range) ===
    if stock.post_earnings_5d_upside_pct > 0:
        # Scale: 10% = 10pts, 20% = 16pts, 30%+ = 20pts (max)
        upside_score = min(stock.post_earnings_5d_upside_pct / 1.5, 20); score += upside_score
        if upside_score >= 10: signals.append(f"+{stock.post_earnings_5d_upside_pct:.0f}% 5-day move")

    # === 4. STRONG BUY COUNT (analyst conviction multiplier -- 2pts per SB, max 20pts) ===
    sb_score = min(stock.strong_buy_rating * 2, 20); score += sb_score

    stock.composite_score = min(score, 100); stock.signals = signals
    return stock.composite_score


def get_earnings_window(days_ahead: int = 14, window_min: int = 1, window_max: int = 14) -> List[str]:
    """Return AI tickers with earnings in the next N days, sorted by days-to-earnings."""
    results = []
    today = datetime.now().date()
    window_end_date = today + timedelta(days=window_max)

    print(f"Scanning for earnings in next {days_ahead} days...")

    for ticker in AI_TICKERS:
        try:
            stock = yf.Ticker(ticker)
            cal = stock.calendar
            if cal and 'Earnings Date' in cal:
                earnings_dates = cal['Earnings Date']
                if isinstance(earnings_dates, list) and earnings_dates:
                    earnings_date = earnings_dates[0]
                    if isinstance(earnings_date, datetime):
                        earnings_date = earnings_date.date()
                    if isinstance(earnings_date, datetime):
                        earnings_date = earnings_date.date()
                    days_out = (earnings_date - today).days
                    if window_min <= days_out <= days_ahead:
                        results.append((ticker, earnings_date, days_out))
                        print(f"  {ticker}: {earnings_date} ({days_out} days)")
        except Exception as e:
            pass

    if not results:
        print("  No earnings found in window. Broadening search...")
        for ticker in AI_TICKERS:
            if ticker in EXCLUDED_TICKERS: continue
            try:
                stock = yf.Ticker(ticker)
                cal = stock.calendar
                if cal and 'Earnings Date' in cal:
                    earnings_dates = cal['Earnings Date']
                    if isinstance(earnings_dates, list) and earnings_dates:
                        earnings_date = earnings_dates[0]
                        if isinstance(earnings_date, datetime):
                            earnings_date = earnings_date.date()
                        days_out = (earnings_date - today).days
                        if 1 <= days_out <= 30:
                            results.append((ticker, earnings_date, days_out))
                            print(f"  {ticker}: {earnings_date} ({days_out} days)")
            except:
                pass

    results.sort(key=lambda x: x[2])
    return [t[0] for t in results]


def analyze_ticker(ticker: str, earnings_date) -> Optional[EarningsSignal]:
    try:
        stock = yf.Ticker(ticker); info = stock.info
        current_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('targetMeanPrice', 0)
        prev_close = info.get('previousClose') or info.get('regularMarketPreviousClose')
        if current_price and prev_close and prev_close > 0:
            price_change_abs = round(current_price - prev_close, 2)
            price_change_pct = round((price_change_abs / prev_close) * 100, 2)
        price_target = info.get('targetMeanPrice', 0) or info.get('targetHighPrice', 0) or 0
        target_upside_pct = ((price_target - current_price) / current_price * 100) if current_price > 0 and price_target > 0 else 0

        # Get actual analyst rating breakdown from yfinance recommendations method
        # This gives us Strong Buy / Buy / Hold / Sell / Strong Sell counts
        strong_buy_rating = 0; buy_rating = 0; buy_rating_pct = 0
        total_analysts = info.get('numberOfAnalystOpinions', 0)
        try:
            rec_df = stock.recommendations
            if rec_df is not None and not rec_df.empty:
                # Prefer '0m' or '-1m' (most recent), fall back to first row
                current_row = rec_df[rec_df['period'].isin(['0m', '-1m'])]
                if current_row.empty:
                    current_row = rec_df.iloc[[0]]
                row = current_row.iloc[0]
                sb = int(row.get('strongBuy', 0))
                b = int(row.get('buy', 0))
                h = int(row.get('hold', 0))
                s = int(row.get('sell', 0))
                ss = int(row.get('strongSell', 0))
                total = sb + b + h + s + ss
                strong_buy_rating = sb
                buy_rating = b
                hold_rating = h
                sell_rating = s + ss
                buy_rating_pct = round((sb + b) / total * 100, 1) if total > 0 else 0
                if total_analysts == 0: total_analysts = total
        except Exception: pass

        # Fallback: if recommendations method didn't work, use info dict
        if strong_buy_rating == 0 and total_analysts > 0:
            rec_key = info.get('recommendationKey', '')
            if 'strong_buy' in rec_key.lower(): strong_buy_rating = max(3, round(total_analysts * 0.6)); buy_rating = max(2, round(total_analysts * 0.3)); buy_rating_pct = 75
            elif rec_key == 'buy': strong_buy_rating = max(2, round(total_analysts * 0.5)); buy_rating = 0; buy_rating_pct = 60
            elif rec_key == 'outperform': strong_buy_rating = max(2, round(total_analysts * 0.5)); buy_rating = 0; buy_rating_pct = 70

        implied_volatility = 0
        post_earnings_target = 0.0
        post_earnings_upside_pct = 0.0
        try:
            opt = stock.option_chain()
            if opt.calls.shape[0] > 0 and opt.puts.shape[0] > 0 and current_price > 0:
                calls = opt.calls.copy()
                puts = opt.puts.copy()
                calls['abs_ITM'] = abs(calls['strike'] - current_price)
                puts['abs_ITM'] = abs(puts['strike'] - current_price)
                atm_call = calls.loc[calls['abs_ITM'].idxmin()]
                atm_put = puts.loc[puts['abs_ITM'].idxmin()]
                call_price = atm_call.get('lastPrice', 0) or atm_call.get('bid', 0) or 0
                put_price = atm_put.get('lastPrice', 0) or atm_put.get('bid', 0) or 0
                straddle_cost = call_price + put_price
                iv_from_straddle = (straddle_cost / current_price) * 100
                if iv_from_straddle > 0:
                    implied_volatility = round(iv_from_straddle, 1)
                    # PE target = current + straddle x1 (conservative sell)
                    post_earnings_target = round(current_price + straddle_cost, 2)
                    post_earnings_upside_pct = round((straddle_cost / current_price) * 100, 1)
                    # 3D target = current + straddle x3 (mid exit)
                    post_earnings_3d_target = round(current_price + straddle_cost * 3, 2)
                    post_earnings_3d_upside_pct = round((straddle_cost * 3 / current_price) * 100, 1)
                    # 5D target = current + straddle x5 (max upside rotation trade)
                    post_earnings_5d_target = round(current_price + straddle_cost * 5, 2)
                    post_earnings_5d_upside_pct = round((straddle_cost * 5 / current_price) * 100, 1)
                else:
                    atm_calls = opt.calls[opt.calls['inTheMoney'] == False]
                    if len(atm_calls) > 0:
                        iv = atm_calls.iloc[0].get('impliedVolatility', 0)
                        implied_volatility = iv * 100 if iv else 0
        except: pass

        # Fallback: if options failed, scale 12-month target down to post-earnings estimate
        if post_earnings_upside_pct == 0 and price_target > 0 and current_price > 0:
            annual_up = ((price_target - current_price) / current_price * 100)
            post_earnings_upside_pct = round(annual_up * 0.4, 1)
            post_earnings_target = round(current_price * (1 + post_earnings_upside_pct / 100), 2)
        short_interest = (info.get('shortPercentOfFloat', 0) or 0) * 100
        avg_volume = info.get('averageVolume', 0) or info.get('averageDailyVolume10Day', 0) or 0
        sector = info.get('sector', 'Technology')
        market_cap_raw = info.get('marketCap', 0) or 0
        company_name = info.get('longName', info.get('shortName', ticker))
        days_to_earnings = (earnings_date - datetime.now().date()).days
        earnings_date_str = earnings_date.strftime('%Y-%m-%d')
        signal = EarningsSignal(ticker=ticker, company_name=company_name, earnings_date=earnings_date_str, days_to_earnings=days_to_earnings,
            current_price=round(current_price,2) if current_price else 0, price_target=round(price_target,2) if price_target else 0,
            target_upside_pct=round(target_upside_pct,1) if target_upside_pct else 0,
            post_earnings_target=post_earnings_target, post_earnings_upside_pct=post_earnings_upside_pct,
            post_earnings_3d_target=post_earnings_3d_target, post_earnings_3d_upside_pct=post_earnings_3d_upside_pct,
            post_earnings_5d_target=post_earnings_5d_target, post_earnings_5d_upside_pct=post_earnings_5d_upside_pct,
            strong_buy_rating=strong_buy_rating, buy_rating=buy_rating, hold_rating=hold_rating, sell_rating=sell_rating,
            total_analysts=total_analysts, buy_rating_pct=buy_rating_pct, implied_volatility=implied_volatility,
            short_interest=round(short_interest,2) if short_interest else 0, avg_volume=avg_volume, sector=sector,
            price_change_pct=price_change_pct, price_change_abs=price_change_abs,
            market_cap=round(market_cap_raw / 1e9, 2) if market_cap_raw else 0)
        calculate_composite_score(signal)
        signal.top_news = fetch_top_news(ticker, count=1)
        return signal
    except Exception as e:
        import traceback; traceback.print_exc(); return None


def generate_html_report(stocks: list, output_path: str):
    import math
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

    def score_color(s):
        return '#00ff88' if round(s) >= 80 else '#58a6ff'

    # Pre-compute all derived values before building HTML
    strong_count = sum(1 for s in stocks if round(s.composite_score) >= 80)
    strong_buys = [s for s in stocks if round(s.composite_score) >= 80]
    pick = sorted(strong_buys, key=lambda x: (x.days_to_earnings, -x.post_earnings_upside_pct, -x.composite_score))[0] if strong_buys else (stocks[0] if stocks else None)
    pick_profit = pick_sell = pick_color = None
    if pick:
        pick_profit = f"+{round(pick.post_earnings_upside_pct, 1)}%" if pick.post_earnings_upside_pct > 0 else 'N/A'
        pick_sell = f"${round(pick.post_earnings_target, 2)}" if pick.post_earnings_target > 0 else 'N/A'
        pick_color = score_color(pick.composite_score)

    # Build rows first
    rows_html = []
    for i, stock in enumerate(stocks[:20], 1):
        color = score_color(stock.composite_score)
        news_lines = ''
        if stock.top_news:
            item = stock.top_news[0]
            if item.get('url'):
                news_lines = '<a href="' + item['url'] + '" target="_blank" rel="noopener noreferrer" style="color:#fff;text-decoration:none">&#128240; ' + item['title'] + '</a>'
            else:
                news_lines = '<span style="color:#fff">&#128240; ' + item['title'] + '</span>'
        days_color = '#00ff88' if stock.days_to_earnings <= 7 else '#ffcc00'
        bg = 'rgba(0,255,136,0.12)' if round(stock.composite_score)>=80 else 'rgba(31,111,235,0.12)'
        #tbody = ''.join(rows_html)

    # Build full HTML
    SCANNER_TITLE = "AI Market Cap Scanner"
    html = '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>' + SCANNER_TITLE + '</title>'
    html += '<style>'
    html += '*{margin:0;padding:0;box-sizing:border-box}body{font-family:Segoe UI,Arial,sans-serif;background:#0d1117;color:#c9d1d9;padding:20px}'
    html += '.header{background:linear-gradient(135deg,#1a1f2e,#161b22);padding:25px;border-radius:12px;margin-bottom:20px;border:1px solid #30363d}'
    html += '.hdr-row{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:15px}'
    html += 'h1{color:#58a6ff;font-size:1.8em;margin-bottom:5px}.desc{color:#fff;font-size:0.95em}'
    html += '.btn{background:#238636;border:none;color:#fff;padding:10px 22px;border-radius:6px;font-size:0.9em;cursor:pointer;font-weight:bold;flex-shrink:0}.btn:hover{background:#2ea043}.btn:disabled{background:#444;cursor:not-allowed}#refreshBtn{background:#1f6feb}#refreshBtn:hover{background:#388bfd}'
    
    html += '.ticker-strip{display:flex;overflow:hidden;white-space:nowrap;background:#0a0f18;border-bottom:1px solid #30363d;padding:8px 0;font-size:0.82em}'
    html += '.ticker-strip-inner{display:flex;gap:0;animation:scroll-ticker 40s linear infinite}'
    html += '.ticker-item{display:inline-flex;align-items:center;gap:6px;padding:0 18px;border-right:1px solid #30363d;flex-shrink:0}'
    html += '.ticker-sym{font-weight:bold;color:#58a6ff}.ticker-price{color:#fff}'
    html += '.ticker-up{color:#00ff88}.ticker-dn{color:#ff6b6b}'
    html += '@keyframes scroll-ticker{0%{transform:translateX(0)}100%{transform:translateX(-50%)}}'
    html += '.ticker-strip:hover .ticker-strip-inner{animation-play-state:paused}'

    html += '.updated{margin-top:12px;color:#6e7681;font-size:0.85em}'
    html += '.warn{margin-top:10px;padding:10px 15px;background:#1f2937;border-left:3px solid #f0883e;border-radius:4px;font-size:0.82em;color:#8b949e;display:none}'
    html += '.legend{display:flex;gap:20px;margin:0;font-size:0.85em;flex-wrap:wrap}.legend span{display:flex;align-items:center;gap:6px}'
    html += '.dot{width:12px;height:12px;border-radius:50%}'
    html += '.stats-bar{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:15px;margin:15px 0}'
    html += '.stat{background:#161b22;padding:12px 18px;border-radius:8px;text-align:center;border:1px solid #30363d;min-width:90px}'
    html += '.stat-val{font-size:1.4em;font-weight:bold;color:#58a6ff}.stat-lbl{font-size:0.75em;color:#8b949e;margin-top:3px}'
    html += 'table{width:100%;border-collapse:collapse;background:#161b22;border-radius:8px;overflow:hidden;margin-top:10px}'
    html += 'th{background:#1f2937;padding:10px 12px;text-align:left;font-size:0.78em;color:#8b949e;text-transform:uppercase;border-bottom:2px solid #30363d;cursor:pointer;user-select:none;white-space:nowrap}th:hover{color:#c9d1d9}thead th{color:#fff!important}thead th:hover{color:#8b949e}thead tr{border-bottom:2px solid #3fb950;box-shadow:0 2px 10px rgba(63,185,80,0.5)}th:hover{color:#c9d1d9}thead th{color:#fff!important}thead th:hover{color:#8b949e}thead tr{border-bottom:2px solid #3fb950;box-shadow:0 2px 10px rgba(63,185,80,0.5)}'
    html += 'th:hover{color:#c9d1d9}'
    html += 'th.sorted-asc::after{content:" ▲";color:#00ff88}'
    html += 'th.sorted-desc::after{content:" ▓";color:#00ff88}'
    html += 'td{padding:10px 10px;border-bottom:1px solid #30363d;font-size:0.88em;color:#fff}td:nth-child(6){border-right:2px solid #3fb950;box-shadow:1px 0 8px rgba(63,185,80,0.5)}tr{height:auto}tr:hover{background:#1c2128}'
    html += '.note{margin-top:20px;padding:12px 18px;background:#161b22;border-radius:8px;font-size:0.82em;color:#8b949e;border:1px solid #30363d}'
    html += '.disclaimer{margin-top:12px;padding:12px 18px;background:#1a1a1a;border-radius:8px;font-size:0.80em;color:#999;border:1px solid #c0392b}'
    html += ".pick-banner{background:linear-gradient(135deg,#2a1a00,#ffd700);border:2px solid #ffd700;border-radius:8px;padding:40px 18px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;min-height:120px}"
    html += '#chat-btn{position:fixed;bottom:24px;right:24px;background:#238636;color:#fff;border:none;border-radius:8px;padding:12px 24px;font-size:0.95em;font-weight:bold;cursor:pointer;box-shadow:0 4px 20px rgba(0,0,0,0.5);z-index:9999;transition:background .2s}@keyframes feat-glow{0%,100%{box-shadow:0 0 8px rgba(255,215,0,.5)}50%{box-shadow:0 0 25px rgba(255,215,0,.9)}}@keyframes sb-glow{0%,100%{box-shadow:0 0 4px rgba(63,185,80,.3)}50%{box-shadow:0 0 10px rgba(63,185,80,.6)}}tr[style*="rgba(0,255,136,0.12)"]{animation:sb-glow 2.5s ease-in-out infinite;border-left:3px solid #3fb950}.pick-banner{animation:feat-glow 2s ease-in-out infinite}'
    html += '#chat-btn:hover{background:#2ea043}'
    html += '#chat-panel{position:fixed;bottom:80px;right:24px;width:360px;max-height:520px;background:#161b22;border:1px solid #30363d;border-radius:12px;box-shadow:0 8px 32px rgba(0,0,0,0.6);display:none;flex-direction:column;z-index:9998;overflow:hidden}'
    html += '#chat-panel.open{display:flex}'
    html += '#chat-header{background:#1f2937;padding:14px 16px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #30363d}'
    html += "#chat-header span{font-weight:bold;color:#58a6ff;font-size:1em}"
    html += "#chat-close{background:none;border:none;color:#8b949e;font-size:1.2em;cursor:pointer;padding:0;line-height:1}#chat-close:hover{color:#fff}"
    html += '#chat-msgs{flex:1;overflow-y:auto;padding:14px 16px;display:flex;flex-direction:column;gap:10px;min-height:200px;max-height:340px}'
    html += ".msg{font-size:0.88em;line-height:1.5;padding:10px 14px;border-radius:10px;max-width:85%}"
    html += ".msg-user{background:#238636;color:#fff;align-self:flex-end;border-bottom-right-radius:3px}"
    html += ".msg-bot{background:#1f2937;color:#c9d1d9;align-self:flex-start;border-bottom-left-radius:3px}"
    html += ".msg-bot.loading{color:#8b949e;font-style:italic}"
    html += '#chat-input-row{display:flex;border-top:1px solid #30363d;padding:10px 12px;gap:8px}'
    html += '#chat-input{flex:1;background:#0d1117;border:1px solid #30363d;border-radius:8px;color:#c9d1d9;padding:8px 12px;font-size:0.88em;resize:none;outline:none;font-family:Segoe UI,Arial,sans-serif}'
    html += '#chat-input:focus{border-color:#58a6ff}'
    html += '#chat-send{background:#238636;border:none;color:#fff;border-radius:8px;padding:8px 16px;font-size:0.88em;cursor:pointer;font-weight:bold}#chat-send:hover{background:#2ea043}#chat-send:disabled{background:#444;cursor:not-allowed}'
    html += '</style></head><body>'

    # Ticker strip
    ticker_items = ''
    for s in stocks:
        chg = s.price_change_pct
        chg_cls = 'ticker-up' if chg >= 0 else 'ticker-dn'
        chg_str = f'+{chg:.2f}%' if chg >= 0 else f'{chg:.2f}%'
        ticker_items += f'<span class=ticker-item><span style="font-weight:bold;color:#00ff88">{round(s.composite_score)}</span> <span class=ticker-sym>{s.ticker}</span> <span class=ticker-price>${round(s.current_price, 2)}</span> <span class="ticker-chg {chg_cls}">{chg_str}</span></span>'
    html += '<div class=ticker-strip><div class=ticker-strip-inner>' + ticker_items + ticker_items + '</div></div>'

    html += '<div class=header><div class=hdr-row><div><h1>' + SCANNER_TITLE + '</h1><div class=desc>Pre-earnings momentum scanner for AI/AI-niche sector | Auto-runs daily at 6:30 AM PT | Subscribe to unlock Run Scan & Chat</div></div>'
    html += '<div style="display:flex;flex-direction:column;gap:8px;align-items:flex-end;margin-left:auto">'
    html += '<div style="display:flex;gap:6px;align-items:center">'
    html += '<span style="background:#161b22;border:1px solid #2ea043;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#2ea043">' + str(strong_count) + '</span> <span style="color:#8b949e">Strong Buy</span></span>'
    html += '<span style="background:#161b22;border:1px solid #1f6feb;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#58a6ff">' + str(sum(1 for s in stocks if round(s.composite_score) < 80)) + '</span> <span style="color:#8b949e">Watch</span></span>'
    html += '<button class=btn id=refreshBtn onclick=refreshData()>Refresh</button>'
    html += "<button class=btn id=scanBtn onclick=runScan()>Run Scan</button>"
    html += '</div></div></div>'
    html += '<div class=warn id=warnMsg></div>'
    html += '<div class=updated>Updated: ' + timestamp + ' | Price data from Yahoo Finance | Options data via Yahoo Finance</div>'
    html += '<div class=stats-bar><div class=legend><span><span class=dot style=background:#00ff88></span> Score 80+: Strong Buy</span><span><span class=dot style=background:#58a6ff></span> Score &lt;80: Watch</span></div></div>'

    if pick:
        html += '<div class=pick-banner style="background:linear-gradient(135deg,#2a1a00,#ffd700);border:2px solid #ffd700;border-radius:8px;padding:40px 18px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:15px 0;min-height:120px">'
        html += '<span style="font-size:1.3em;color:#2ea043;font-weight:bold">&#9733; AI\'s Suggested Trade</span>'
        html += '<span style="font-size:1.2em;font-weight:bold;color:#fff">' + pick.ticker + '</span>'
        html += '<span style="font-size:0.95em;color:#8b949e">' + pick.company_name[:28] + ('...' if len(pick.company_name) > 28 else '') + '</span>'
        html += '<span style="font-size:0.95em;color:#8b949e">Score: <strong style="color:' + pick_color + '">' + str(round(pick.composite_score)) + '</strong></span>'
        html += '<span style="font-size:0.95em;color:#8b949e">Price: <strong style="color:#00ff88">$' + str(round(pick.current_price, 2)) + '</strong></span>'
        html += '<span style="font-size:0.95em;color:#8b949e">Sell: <strong style="color:#58a6ff">' + pick_sell + '</strong></span>'
        html += '<span style="font-size:0.95em;color:#8b949e">Earnings in: <strong style="color:#ffcc00">' + str(pick.days_to_earnings) + ' days</strong></span>'
        html += '<span style="font-size:0.95em;color:#8b949e">PE Profit: <strong style="color:#00ff88;font-weight:bold">' + pick_profit + '</strong></span>'
        html += '</div>'

    headers = [
        ('Ticker','ticker'), ('Company','company_name'), ('Score','score'),
        ('Next Earnings','earnings_date'), ('Days<br>Left','days_left'), ('Current<br>Price','price'),
        ('Post Earnings<br>Target','pe_target'), ('Great Earnings Report','3d'), ('Excellent Earnings Report','5d'),
        ('Analyst<br>Reports','analysts'), ('S-BUY','sb'), ('Buy','buy'),
        ('Hold','hold'), ('Sell','sell'), ('Market Cap','mktcap'), ('News','news')
    ]
    ths = ''
    for h, col in headers:
        ths += '<th onclick="sortBy(\'' + col + '\')" data-col="' + col + '">' + h + '</th>'
    html += '<table id="stockTable"><thead><tr>' + ths + '</tr></thead><tbody id="stockTableBody">'

    rows_data = []
    for i, stock in enumerate(stocks[:20], 1):
        rows_data.append({
            'rank': i, 'ticker': stock.ticker, 'company_name': stock.company_name,
            'score': round(stock.composite_score), 'earnings_date': stock.earnings_date,
            'days_left': stock.days_to_earnings, 'price': round(stock.current_price, 2),
            'pe_target': round(stock.post_earnings_target, 2), 'pe_upside': round(stock.post_earnings_upside_pct, 1),
            '3d': round(stock.post_earnings_3d_target, 2), '3d_up': round(stock.post_earnings_3d_upside_pct, 1),
            '5d': round(stock.post_earnings_5d_target, 2), '5d_up': round(stock.post_earnings_5d_upside_pct, 1),
            'analysts': stock.total_analysts, 'sb': stock.strong_buy_rating,
            'buy': stock.buy_rating, 'hold': stock.hold_rating, 'sell': stock.sell_rating,
            'mktcap': stock.market_cap,
            'news': stock.top_news[0] if stock.top_news else None
        })

    import json
    # Build static table rows in Python - no JS needed for display
    def score_color_css(score):
        return '#00ff88' if score >= 80 else '#58a6ff'
    def row_bg(score):
        return 'rgba(0,255,136,0.12)' if score >= 80 else 'rgba(31,111,235,0.12)'
    def days_color(days):
        return '#00ff88' if days <= 7 else '#ffcc00'
    def news_link(news):
        if not news:
            return '&#128240; --'
        url = news.get('url', '')
        title = news.get('title', '')
        if url:
            return '<a href="' + url + '" target="_blank" style="color:#fff;text-decoration:none">&#128240; ' + title[:60] + '</a>'
        return '<span style="color:#fff">&#128240; ' + title[:60] + '</span>'
    def fmt_mktcap(val):
        if val >= 1000:
            return '$' + str(round(val / 1000, 2)) + 'T'
        elif val >= 1:
            return '$' + str(round(val, 2)) + 'B'
        else:
            return '$' + str(round(val * 1000, 0)) + 'M'

    static_rows = ''
    for r in rows_data:
        c_color = score_color_css(r['score'])
        bg_color = row_bg(r['score'])
        d_color = days_color(r['days_left'])
        co_name = r['company_name'][:35] + ('...' if len(r['company_name']) > 35 else '')
        news_cell = news_link(r['news'])
        static_rows += '<tr style="background:' + bg_color + '">'
        static_rows += '<td><strong><a href="https://finance.yahoo.com/quote/' + r['ticker'] + '" target="_blank" style="color:#66b2ff">' + r['ticker'] + '</a></strong></td>'
        static_rows += '<td>' + co_name + '</td>'
        static_rows += '<td><strong style="color:' + c_color + '">' + str(r['score']) + '</strong></td>'
        static_rows += '<td>' + r['earnings_date'] + '</td>'
        static_rows += '<td style="color:' + d_color + ';font-weight:bold">' + str(r['days_left']) + 'd</td>'
        static_rows += '<td style="font-weight:bold">$' + str(r['price']) + '</td>'
        static_rows += '<td style="font-weight:bold">$' + str(r['pe_target']) + '<br><span style="color:#00ff88">+' + str(r['pe_upside']) + '%</span></td>'
        static_rows += '<td>$' + str(r['3d']) + '<br><span style="color:#00ff88">+' + str(r['3d_up']) + '%</span></td>'
        static_rows += '<td>$' + str(r['5d']) + '<br><span style="color:#00ff88">+' + str(r['5d_up']) + '%</span></td>'
        static_rows += '<td>' + str(r['analysts']) + '</td>'
        static_rows += '<td style="color:#00ff88">' + str(r['sb']) + '</td>'
        static_rows += '<td style="color:#58a6ff">' + str(r['buy']) + '</td>'
        static_rows += '<td style="color:#ffcc00">' + str(r['hold']) + '</td>'
        static_rows += '<td style="color:#ff6b6b">' + str(r['sell']) + '</td>'
        static_rows += '<td>' + fmt_mktcap(r['mktcap']) + '</td>'
        static_rows += '<td>' + news_cell + '</td>'
        static_rows += '</tr>'

    html += static_rows + '</tbody></table>'
    html += '<script>var rowsData=' + json.dumps(rows_data) + ';\n'
    html += "var sortCol='days_left';var sortAsc=true;function getVal(r,col){var m={'ticker':r.ticker,'company_name':r.company_name,'score':r.score,'earnings_date':r.earnings_date,'days_left':r.days_left,'price':r.price,'pe_target':r.pe_target,'3d':r['3d'],'5d':r['5d'],'analysts':r.analysts,'sb':r.sb,'buy':r.buy,'hold':r.hold,'sell':r.sell,'mktcap':r.mktcap'};return m[col]||r[col]||0;}function updateArrows(){document.querySelectorAll('th[data-col]').forEach(function(th){th.classList.remove('sorted-asc','sorted-desc');});var th=document.querySelector('th[data-col=\"'+sortCol+'\"]');if(th){th.classList.add(sortAsc?'sorted-asc':'sorted-desc');}}function sortBy(col){if(sortCol===col){sortAsc=!sortAsc;}else{sortCol=col;sortAsc=col==='days_left'||col==='score'||col==='analysts'||col==='sb'||col==='buy'||col==='hold'||col==='sell'||col==='price'||col==='pe_target'||col==='3d'||col==='5d'||col==='mktcap';}var dirs={'ticker':1,'company_name':1};var asc=dirs[col]?sortAsc:!sortAsc;rowsData.sort(function(a,b){var va=getVal(a,col),vb=getVal(b,col);if(typeof va==='number')return asc?va-vb:vb-va;return asc?String(va).localeCompare(String(vb)):String(vb).localeCompare(String(va));});renderTable();updateArrows();}function fmtMktcap(v){if(v>=1000)return'$'+Math.round(v/1000*100)/100+'T';if(v>=1)return'$'+Math.round(v*100)/100+'B';return'$'+Math.round(v*1000)+'M';}function scoreColor(s){return s>=80?'#00ff88':'#58a6ff';}function newsHtml(n){if(!n)return'';var u=n.url||'';var t=n.title||'';return u?'<a href=\"'+u+'\" target=\"_blank\" style=\"color:#fff;text-decoration:none\">&#128240; '+t+'</a>':'<span style=\"color:#fff\">&#128240; '+t+'</span>';}function renderTable(){var tbody=document.getElementById('stockTableBody');if(!tbody)return;var html='';rowsData.forEach(function(r){var c=scoreColor(r.score);var bg=r.score>=80?'rgba(0,255,136,0.12)':'rgba(31,111,235,0.12)';html+='<tr style=\"background:'+bg+'\"><td><strong><a href=\"https://finance.yahoo.com/quote/'+r.ticker+'\" target=\"_blank\" style=\"color:#66b2ff\">'+r.ticker+'</a></strong></td>';html+='<td>'+r.company_name.substring(0,35)+(r.company_name.length>35?'...':'')+'</td>';html+='<td><strong style=\"color:'+c+'\">'+r.score+'</strong></td>';html+='<td>'+r.earnings_date+'</td>';html+='<td style=\"color:'+(r.days_left<=7?'#00ff88':'#ffcc00')+';font-weight:bold\">'+r.days_left+'d</td>';html+='<td>$'+r.price+'</td>';html+='<td>$'+r.pe_target+' | +'+r.pe_upside+'%</td>';html+='<td>$'+r['3d']+' | +'+r['3d_up']+'%</td>';html+='<td>$'+r['5d']+' | +'+r['5d_up']+'%</td>';html+='<td>'+r.analysts+'</td>';html+='<td style=\"color:#00ff88\">'+r.sb+'</td>';html+='<td style=\"color:#58a6ff\">'+r.buy+'</td>';html+='<td style=\"color:#ffcc00\">'+r.hold+'</td>';html+='<td style=\"color:#ff6b6b\">'+r.sell+'</td>';html+='<td>'+fmtMktcap(r.mktcap)+'</td>';html+='<td>'+newsHtml(r.news)+'</td></tr>';});tbody.innerHTML=html;};sortBy('days_left');"

    html += '</script>'
    html += '<div class=note><b>Scoring:</b> Analyst (30pts) + Buy% (30pts) + 5D Upside (20pts) + SB Count (2pts each, max 20) | <b>PE Target:</b> straddle x1 (conservative) | <b>3-Day Momentum:</b> straddle x3 (mid) | <b>5-Day Momentum:</b> straddle x5 (max upside) | <b>Entry:</b> 1-14 days pre-earnings | <b>Exit:</b> 1-5 days after beat</div>'
    html += '<div class=disclaimer>&#9888; <b>Not a financial advisor.</b> This scanner is for informational purposes only. Options data and targets are estimates based on ATM straddles -- actual results may vary. Stocks carry risk; always do your own research before trading. I am not liable for any losses incurred from trades based on this data.</div>'
    html += "<script>var scanBtn=document.getElementById('scanBtn');var warnMsg=document.getElementById('warnMsg');function runScan(){if(scanBtn.disabled)return;scanBtn.disabled=true;warnMsg.textContent='Starting scanner...';var serverWin=window.open('about:blank','scanner_window','width=400,height=200');if(!serverWin){warnMsg.textContent='Popup blocked! Allow popups for this site.';scanBtn.disabled=false;return;}serverWin.document.write('<html><body style=\"font-family:Arial;background:#1a1a2e;color:#fff;padding:20px\"><h3>AI Market Cap Scanner</h3><p>Starting scan server...</p><p>If this window doesn\\'t close in 5 seconds, <a href=\"http://localhost:18765/run\" target=\"_blank\">click here</a> after starting scanner_web.py</p><script>fetch(\\'http://localhost:18765/run\\',{method:\\'POST\\'}).then(()=>{document.body.innerHTML=\\'<p>Scan started! This window will close.</p>\\';setTimeout(()=>window.close(),2000);}).catch(e=>{document.body.innerHTML=\\'<p style=\"color:#ff6b6b\">Error: Make sure scanner_web.py is running!</p><button onclick=\\\"window.close()\\\">Close</button>\\';});<\\/script></body></html>');setTimeout(function(){warnMsg.textContent='Server launched! Reloading scanner...';location.reload(true);},3000);}function refreshData(){location.reload(true);}</script>"

    # Chat widget - clean plain JS, no HTML entities
    html += '<button id="chat-btn" onclick="toggleChat()">Chat</button>'
    html += '<div id="chat-panel">'
    html += '<div id="chat-header"><span>AI Scanner Assistant</span><button id="chat-close" onclick="toggleChat()">X</button></div>'
    html += '<div id="chat-msgs"><div class="msg msg-bot">Hi! I can answer questions about how the scanner works, what the scores mean, or how to read the trade signals.</div></div>'
    html += '<div id="chat-input-row"><input id="chat-input" type="text" placeholder="Ask a question..." onkeydown="if(event.key===\'Enter\'&&!event.shiftKey)sendMsg()"/><button id="chat-send" onclick="sendMsg()">Send</button></div>'
    html += '</div>'
    html += '<script>'
    html += 'var chatOpen=false;'
    html += 'function toggleChat(){chatOpen=!chatOpen;var p=document.getElementById("chat-panel");if(chatOpen){p.style.display="flex";}else{p.style.display="none";}}'
    html += 'function sendMsg(){'
    html += 'var i=document.getElementById("chat-input");'
    html += 'var m=i.value.trim();'
    html += 'if(!m)return;'
    html += 'var ms=document.getElementById("chat-msgs");'
    html += 'var userDiv=document.createElement("div");'
    html += 'userDiv.className="msg msg-user";'
    html += 'userDiv.textContent=m;'
    html += 'ms.appendChild(userDiv);'
    html += 'ms.scrollTop=ms.scrollHeight;'
    html += 'i.value="";'
    html += 'var b=document.getElementById("chat-send");'
    html += 'b.disabled=true;'
    html += 'b.textContent="...";'
    html += 'var loadingDiv=document.createElement("div");'
    html += 'loadingDiv.className="msg msg-bot loading";'
    html += 'loadingDiv.textContent="Thinking...";'
    html += 'ms.appendChild(loadingDiv);'
    html += 'ms.scrollTop=ms.scrollHeight;'
    html += 'fetch("/api/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:m})}).then(function(r){return r.ok?r.json():Promise.reject("Server error");}).then(function(d){'
    html += 'loadingDiv.remove();'
    html += 'var botDiv=document.createElement("div");'
    html += 'botDiv.className="msg msg-bot";'
    html += 'botDiv.textContent=d.reply||"Got it.";'
    html += 'ms.appendChild(botDiv);'
    html += 'ms.scrollTop=ms.scrollHeight;'
    html += '}).catch(function(e){'
    html += 'loadingDiv.remove();'
    html += 'var errDiv=document.createElement("div");'
    html += 'errDiv.className="msg msg-bot";'
    html += 'errDiv.textContent="Error: "+e;'
    html += 'ms.appendChild(errDiv);'
    html += 'ms.scrollTop=ms.scrollHeight;'
    html += '}).finally(function(){'
    html += 'b.disabled=false;'
    html += 'b.textContent="Send";'
    html += '});'
    html += '}'
    html += '</script>'
    html += "</body></html>"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"HTML saved: {output_path} (size: {len(html)} bytes)")

def generate_csv_report(stocks: list, output_path: str):
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['Rank','Ticker','Company','Days to Earnings','Earnings Date','Current Price','PE Target','PE Upside %','3D Target','3D Upside %','5D Target','5D Upside %','# of Analyst','Strong Buy Ratings','Buy Ratings','Hold Ratings','Sell Ratings','Composite Score','Signals','Top News'])
        for i, stock in enumerate(stocks, 1):
            w.writerow([i, stock.ticker, stock.company_name, stock.days_to_earnings, stock.earnings_date, stock.current_price, stock.post_earnings_target, stock.post_earnings_upside_pct, stock.post_earnings_3d_target, stock.post_earnings_3d_upside_pct, stock.post_earnings_5d_target, stock.post_earnings_5d_upside_pct, stock.total_analysts, stock.strong_buy_rating, stock.buy_rating, stock.hold_rating, stock.sell_rating, stock.composite_score, ' | '.join(stock.signals) if stock.signals else '', stock.top_news[0]['title'] + ' | ' + stock.top_news[0].get('url','') if stock.top_news else ''])
    print(f"CSV saved: {output_path}")


# Manual earnings date overrides (when yfinance has wrong date)
EARNINGS_OVERRIDES = {
    
}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--days', type=int, default=14, help='Days ahead to scan (1-14)'); parser.add_argument('--top', type=int, default=20)
    args = parser.parse_args()
    print("AI Earnings Scanner - Pre-Earnings Momentum (1-14 Day Window)"); print("="*55)
    if not YF_AVAILABLE: print("ERROR: yfinance not installed. Run: python -m pip install yfinance"); sys.exit(1)

    # Fetch dynamic AI stock list from finviz (Technology sector = broad AI coverage)
    print("Fetching AI stocks from finviz screener...")
    all_tickers = fetch_ai_stocks_from_finviz()
    print(f"Total stocks to scan: {len(all_tickers)}")

    # First scan to get all earnings in window with real dates
    all_results = []
    today = datetime.now().date()
    for ticker in all_tickers:
        if ticker in EXCLUDED_TICKERS: continue
        try:
            if ticker in EARNINGS_OVERRIDES:
                edate = EARNINGS_OVERRIDES[ticker]
                days_out = (edate - today).days
                if 1 <= days_out <= args.days:
                    all_results.append((ticker, edate, days_out))
            else:
                stock = yf.Ticker(ticker)
                cal = stock.calendar
                if cal and 'Earnings Date' in cal:
                    ed = cal['Earnings Date']
                    if isinstance(ed, list) and ed:
                        edate = ed[0]
                        if hasattr(edate, 'date'): edate = edate.date()
                        days_out = (edate - today).days
                        if 1 <= days_out <= args.days:
                            all_results.append((ticker, edate, days_out))
        except Exception as e:
            pass  # Skip tickers that 404 or have errors

    all_results.sort(key=lambda x: x[2])
    print(f"Found {len(all_results)} AI stocks with earnings in next {args.days} days:")
    for t, d, n in all_results:
        print(f"  {t}: {d} ({n} days)")

    stocks = []
    for ticker, edate, days_out in all_results:
        print(f"   Analyzing {ticker}...", end=' ')
        try:
            signal = analyze_ticker(ticker, edate)
            if signal and signal.current_price > 0:
                stocks.append(signal); print(f"Score: {signal.composite_score:.0f}")
            else: print(f"No data (price={signal.current_price if signal else 0})")
        except Exception as e:
            import traceback; traceback.print_exc()
            print(f"Error: {e}")

    stocks.sort(key=lambda x: x.composite_score, reverse=True)
    print(f"Top picks:")
    for i, stock in enumerate(stocks[:5], 1): print(f"   {i}. {stock.ticker}: {stock.composite_score:.0f} | {stock.signals[0] if stock.signals else 'No strong signal'}")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M'); out_dir = os.path.dirname(__file__) or '.'
    html_path = os.path.join(out_dir, f'ai_earnings_57day_{timestamp}.html')
    csv_path = os.path.join(out_dir, f'ai_earnings_57day_{timestamp}.csv')
    print(f"Generating HTML report...")
    generate_html_report(stocks[:args.top], html_path)
    print(f"Generating CSV report...")
    generate_csv_report(stocks, csv_path)
    print("Done!")


if __name__ == '__main__': main()
