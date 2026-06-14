"""AI Earnings Scanner - Pre-Earnings Momentum Strategy (1-45 day window)"""
import argparse, csv, os, sys, time
from datetime import datetime, timedelta, timezone
import time as _time
from dataclasses import dataclass
from typing import List, Optional

PT = timezone(timedelta(hours=-7))

LOCAL_MODE = False

try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False


months_map = {"01":"January","02":"February","03":"March","04":"April","05":"May","06":"June",
          "07":"July","08":"August","09":"September","10":"October","11":"November","12":"December"}

def fmt_date(ed):
    if not ed:
        return ""
    parts = ed.split("-")
    if len(parts) == 3:
        yyyy, mm, dd = parts
        return months_map.get(mm, mm) + " " + str(int(dd)) + ", " + yyyy
    return ed

def get_earnings_with_retry(ticker: str, retries: int = 3, delay: float = 0.3):
    """Fetch yfinance calendar with retry on failure."""
    for attempt in range(retries):
        try:
            stock = yf.Ticker(ticker)
            cal = stock.calendar
            if cal and 'Earnings Date' in cal:
                return cal
            # Empty response - retry
            if attempt < retries - 1:
                _time.sleep(delay)
                continue
        except Exception as e:
            if attempt < retries - 1:
                _time.sleep(delay)
                continue
            else:
                print(f"  [WARN] {ticker}: yfinance failed after {retries} attempts ({e})")
    return None


def get_earnings_sentiment(ticker: str) -> str:
    """Return 'Positive' | 'Mixed' | 'Negative' based on last 4 qtrs EPS surprise %."""
    try:
        t = yf.Ticker(ticker)
        eh = t.earnings_history
        if eh is None or len(eh) == 0:
            return ''
        surprises = []
        for _, row in eh.iterrows():
            sp = row.get('surprisePercent', 0) or row.get('Surprise %', 0)
            if sp is not None and sp != 0:
                surprises.append(float(sp))
        if not surprises:
            return ''
        avg = sum(surprises) / len(surprises)
        # surprisePercent is stored as decimal (0.13 = 13%), convert to % for thresholds
        avg_pct = avg * 100
        if avg_pct > 5:
            return 'Positive'
        elif avg_pct < -5:
            return 'Negative'
        else:
            return 'Mixed'
    except:
        return ''


def fetch_ai_stocks_from_finviz() -> List[str]:
    """Fetch tech sector stocks $10B+ market cap from finviz (cap_large + cap_mega = $10B+)."""
    try:
        import requests
        from bs4 import BeautifulSoup
        tickers = set()
        # cap_large ($10B-$200B) + cap_mega ($200B+) = everything $10B+
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
        print(f"[AI Stocks] Fetched {len(result)} tech stocks ($10B+ mcap) from finviz")
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
                        if len(title_clean) > 45:
                            cutoff = title_clean[:45]
                            last_space = cutoff.rfind(' ')
                            remainder = title_clean[last_space+1:last_space+16]
                            title_clean = cutoff[:last_space] + ' ' + remainder if last_space > 20 else title_clean[:45]
                            title_clean += '...'
                        headlines.append({'title': title_clean, 'url': url})
                        if len(headlines) >= count:
                            break
    except Exception:
        pass
    return headlines
# AI Infrastructure
AI_TICKERS = [
    # SEMICONDUCTORS / AI CHIP (45)
    'NVDA', 'AMD', 'AVGO', 'MRVL', 'INTC', 'QCOM', 'MU', 'TXN', 'LRCX', 'ASML', 'KLAC', 'AMAT', 'SNPS', 'CDNS', 'CRDO',
    'TSM', 'SMCI', 'MCHP', 'NXPI', 'ON', 'MPWR', 'QRVO', 'SWKS', 'TER', 'GEN', 'KEYS', 'FORM', 'SLAB', 'KLA', 'VEECO',
    'ENTG', 'ANSS', 'CAMT', 'CRSR', 'LOGI', 'DIOD', 'MXL', 'LSCC', 'POWI', 'LNW', 'ICR', 'CCMP', 'ADI', 'MSTR', 'COIN', 'RIOT',
    # AI CLOUD / HYPERSCALER (18)
    'MSFT', 'GOOGL', 'AMZN', 'ORCL', 'NOW', 'SNOW', 'CRM', 'WDAY', 'INTU', 'SAP', 'DBX', 'ZM', 'VEEV', 'TEAM', 'ADSK', 'CTSH', 'FICO',
    # CYBERSECURITY (18)
    'PANW', 'CRWD', 'ZS', 'FTNT', 'NET', 'OKTA', 'SPLK', 'HUBS', 'FROG', 'CFLT', 'GLOB', 'SUMO', 'UI', 'GTLB', 'U', 'APP', 'BILL', 'INOD',
    # AI DATA / ANALYTICS (16)
    'DDOG', 'PLTR', 'HPC', 'GRAB', 'MDB', 'EPAM', 'DNLI', 'GTLB', 'U', 'AI', 'PRGS', 'BKI', 'PLAN', 'U', 'MDB', 'EPAM',
    # DEV TOOLS / IT MANAGEMENT (16)
    'WIX', 'DOCU', 'TWLO', 'SMAR', 'PCTY', 'COIN', 'SQSP', 'ZEN', 'PATH', 'ASAN', 'NCNO', 'EVBG', 'NTNX', 'DT', 'ZEN', 'SMAR',
    # FINTECH / PAYMENTS (18)
    'V', 'MA', 'PYPL', 'SQ', 'AFRM', 'SOFI', 'UPST', 'GPN', 'FIS', 'FISV', 'NAVI', 'ALLY', 'WAL', 'HOOD', 'NU', 'RELY', 'GLE', 'RNR',
    # EV / CLEAN ENERGY / SOLAR (20)
    'TSLA', 'ENPH', 'SEDG', 'FSLR', 'RUN', 'NEE', 'BE', 'SMR', 'CEG', 'VST', 'ENLV', 'AMCR', 'JKS', 'NOVA', 'CLNE', 'MAXN', 'SUNW', 'ENPH', 'SEDG', 'FSLR',
    # BIOTECH / HEALTH AI (20)
    'MRNA', 'EXAS', 'ILMN', 'BIIB', 'REGN', 'VRTX', 'ISRG', 'DXCM', 'ALGN', 'TECH', 'BMRN', 'EXEL', 'IDXX', 'IQV', 'STE', 'MTD', 'RMD', 'SYK', 'ZBH', 'EW',
    # MEDIA / STREAMING (14)
    'NFLX', 'DIS', 'WBD', 'PARA', 'ROKU', 'PENN', 'DKNG', 'META', 'SPOT', 'SNAP', 'LYV', 'PARA', 'WBD', 'NFLX',
    # HARDWARE / INFRASTRUCTURE (18)
    'AAPL', 'DELL', 'HPQ', 'HPE', 'ANET', 'PTC', 'SWK', 'ITW', 'PH', 'PKE', 'ESIO', 'HOLX', 'VRSN', 'GEHC', 'CDW', 'NTAP', 'WDC', 'STX',
    # DEFENSE / AEROSPACE TECH (16)
    'BA', 'LMT', 'RTX', 'NOC', 'GD', 'LHX', 'TDY', 'HII', 'SAIC', 'CACI', 'LDOS', 'TXT', 'AIMC', 'AIR', 'OHI', 'DCO',
    # ROBOTICS / INDUSTRIAL AI (16)
    'IRBT', 'ROK', 'EMR', 'HON', 'ETN', 'AME', 'JCI', 'KOD', 'PRLB', 'PLOW', 'MEC', 'ROK', 'EMR', 'ITW', 'PH', 'CARR',
    # SEMI MATERIALS / CHEMICALS (12)
    'APD', 'IFF', 'ECL', 'SHW', 'PPG', 'RPM', 'ALB', 'SCCO', 'LYB', 'CE', 'ALB', 'SCCO',
    # SOFTWARE / ENTERPRISE (18)
    'ADBE', 'VMW', 'CSCO', 'ANSS', 'TTD', 'MRVI', 'GOOG', 'FAST', 'U', 'APP', 'BILL', 'INOD', 'DDOG', 'GTLB', 'NOW', 'CRM', 'ORCL', 'SAP',
    # GAMING (10)
    'EA', 'TTWO', 'NTDOY', 'GAME', 'IMPP', 'BILI', 'SE', 'RBLX', 'MU', 'TTD',
    # INTERNET PLATFORMS (14)
    'META', 'PINS', 'SNAP', 'SPOT', 'ROKU', 'LYFT', 'BIDU', 'BILI', 'CPNG', 'GRAB', 'MELI', 'SHOP', 'SE', 'META',
    # ELECTRONICS / COMPONENTS (14)
    'AVY', 'EL', 'GWW', 'PCAR', 'WSO', 'WST', 'RHI', 'TT', 'CPRT', 'EFX', 'INFO', 'FFIV', 'JKHY', 'FICO',
    # DATACENTER (12)
    'VNET', 'ZTO', 'JD', 'BIDU', 'TCEHY', 'TME', 'IQ', 'YY', 'MOMO', 'TAL', 'EDU', 'BZUN',
    # ADVERTISING (12)
    'IPG', 'OMC', 'NWS', 'NWSA', 'FOX', 'FOXA', 'GCI', 'INMA', 'INOC', 'INVE', 'CTVA', 'MSGW',
    # CUSTOM SILICON / AI ASIC (8)
    'GOOG', 'AMZN', 'MSFT', 'META', 'NVDA', 'AMD', 'MRVL', 'INTC',
    # SMART BUILDING / IoT (8)
    'HON', 'EMR', 'SCHN', 'JCI', 'ETN', 'ROK', 'ABM', 'ESNT',
    # SPACE / SATELLITE TECH (10)
    'ASTS', 'RKLB', 'MAXR', 'SESG', 'IRDM', 'LLAWW', 'VOX', 'SATL', 'Astra', 'SpaceX',
    # AUTONOMOUS VEHICLES / LIDAR (10)
    'LAZR', 'CPTN', 'INVZ', 'MBLY', 'GOOG', 'TSLA', 'NVDA', 'INTC', 'QCOM', 'AAPL',
    # AI AGENTS / AUTOMATION (12)
    'AI', 'U', 'PATH', 'NOW', 'CRM', 'WDAY', 'ASAN', 'TEAM', 'ADSK', 'VEEV', 'HUBS', 'FROG',
    # SMART INFRASTRUCTURE / GRID (10)
    'VRT', 'ETN', 'XYL', 'FE', 'AES', 'EIX', 'NEE', 'DUK', 'SO', 'D',
    # SPATIAL COMPUTING / AR / VR (8)
    'SONY', 'SNAP', 'META', 'U', 'APP', 'PLTR', 'U', 'SNAP',
    # AI PRECISION AGRICULTURE (8)
    'TRMB', 'AGCO', 'DE', 'F', 'CAT', 'ROK', 'AMAT', 'LRCX',
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
    earnings_sentiment: str = ''  # 'Positive' | 'Mixed' | 'Negative' based on last 4 qtrs earnings surprise
    composite_score: float = 0.0; signals: List[str] = None
    top_news: List[str] = None; price_change_pct: float = 0.0; price_change_abs: float = 0.0
    def __post_init__(self):
        if self.signals is None: self.signals = []
        if self.top_news is None: self.top_news = []


def calculate_composite_score(stock: EarningsSignal) -> float:
    score = 0.0; signals = []

    # === 1. ANALYST COVERAGE (25pts max) ===
    # 1pt each, linear to 25
    analyst_score = min(stock.total_analysts, 25)
    score += analyst_score
    if stock.total_analysts >= 10:
        signals.append(f'{stock.total_analysts} analysts')

    # === 2. BUY % CONVICTION (25pts max) ===
    # % of bullish analysts (SB + B out of all ratings)
    if stock.total_analysts > 0:
        bullish = stock.strong_buy_rating + stock.buy_rating
        total_ratings = bullish + stock.hold_rating + stock.sell_rating
        if total_ratings > 0:
            buy_pct = (bullish / total_ratings) * 100
            buy_score = min(buy_pct * 0.25, 25)  # 100% bullish = 25pts
            score += buy_score
            if buy_pct >= 75:
                signals.append(f'{buy_pct:.0f}% bullish ({stock.strong_buy_rating} SB + {stock.buy_rating} B)')

    # === 3. STRONG BUY COUNT (20pts max) ===
    # 2pts each
    sb_score = min(stock.strong_buy_rating * 2, 20)
    score += sb_score

    # === 4. 5D UPSIDE (15pts max) ===
    # Options implied move — 15% move = 15pts
    if stock.post_earnings_5d_upside_pct > 0:
        upside_score = min(stock.post_earnings_5d_upside_pct, 15)
        score += upside_score
        if upside_score >= 10:
            signals.append(f"+{stock.post_earnings_5d_upside_pct:.0f}% implied move")

    # === 5. EARNINGS SENTIMENT (15pts max) ===
    # Recent beat/miss history
    if stock.earnings_sentiment == 'Positive':
        score += 15
        signals.append('Positive earnings trend')
    elif stock.earnings_sentiment == 'Mixed':
        score += 7
        signals.append('Mixed earnings trend')
    elif stock.earnings_sentiment == 'Negative':
        score += 0  # No points for negative

    # Cap at 100
    stock.composite_score = min(score, 100); stock.signals = signals
    return stock.composite_score


def get_earnings_window(days_ahead: int = 45, window_min: int = 0, window_max: int = 45) -> List[str]:
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
                        if 1 <= days_out <= 45:
                            results.append((ticker, earnings_date, days_out))
                            print(f"  {ticker}: {earnings_date} ({days_out} days)")
            except:
                pass

    results.sort(key=lambda x: x[2])
    return [t[0] for t in results]


def analyze_ticker(ticker: str, earnings_date, retries: int = 2) -> Optional[EarningsSignal]:
    for attempt in range(retries):
        try:
            stock = yf.Ticker(ticker); info = stock.info
            current_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('targetMeanPrice', 0)
            if not current_price or current_price == 0:
                if attempt < retries - 1:
                    continue
                return None
            prev_close = info.get('previousClose') or info.get('regularMarketPreviousClose')
            price_change_abs = price_change_pct = 0
            if current_price and prev_close and prev_close > 0:
                price_change_abs = round(current_price - prev_close, 2)
                price_change_pct = round((price_change_abs / prev_close) * 100, 2)
            price_target = info.get('targetMeanPrice', 0) or info.get('targetHighPrice', 0) or 0
            target_upside_pct = ((price_target - current_price) / current_price * 100) if current_price > 0 and price_target > 0 else 0

            # Get actual analyst rating breakdown from yfinance recommendations method
            # This gives us Strong Buy / Buy / Hold / Sell / Strong Sell counts
            strong_buy_rating = 0; buy_rating = 0; hold_rating = 0; sell_rating = 0; buy_rating_pct = 0
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
                    total_analysts = total
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
            post_earnings_3d_target = 0.0
            post_earnings_3d_upside_pct = 0.0
            post_earnings_5d_target = 0.0
            post_earnings_5d_upside_pct = 0.0
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
            # Fetch earnings sentiment from last 4 quarters (MUST be before calculate_composite_score)
            earnings_sentiment = get_earnings_sentiment(ticker)
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
                market_cap=round(market_cap_raw / 1e9, 2) if market_cap_raw else 0,
                earnings_sentiment=earnings_sentiment)
            calculate_composite_score(signal)
            signal.top_news = fetch_top_news(ticker, count=1)
            return signal
        except Exception as e:
            import traceback; traceback.print_exc()
    return None


def generate_html_report(stocks: list, output_path: str):
    import math
    timestamp = datetime.now(PT).strftime('%B %d, %Y at %I:%M %p PT')

    def score_color(s):
        return '#00ff88' if round(s) >= 75 else '#58a6ff'

    # Pre-compute all derived values before building HTML
    strong_count = sum(1 for s in stocks if round(s.composite_score) >= 75)
    strong_buys = [s for s in stocks if round(s.composite_score) >= 75]
    strong_buys.sort(key=lambda x: -x.post_earnings_5d_upside_pct)
    pick = strong_buys[0] if strong_buys else (stocks[0] if stocks else None)
    pick2 = strong_buys[1] if len(strong_buys) > 1 else None
    pick_profit = pick_sell = pick_color = None
    pick2_profit = pick2_sell = pick2_color = None
    if pick:
        pick_profit = f"+{round(pick.post_earnings_upside_pct, 1)}%" if pick.post_earnings_upside_pct > 0 else 'N/A'
        pick_sell = f"${round(pick.post_earnings_target, 2)}" if pick.post_earnings_target > 0 else 'N/A'
        pick_color = score_color(pick.composite_score)
    if pick2:
        pick2_profit = f"+{round(pick2.post_earnings_upside_pct, 1)}%" if pick2.post_earnings_upside_pct > 0 else 'N/A'
        pick2_sell = f"${round(pick2.post_earnings_target, 2)}" if pick2.post_earnings_target > 0 else 'N/A'
        pick2_color = '#58a6ff'

    # Build rows first
    rows_html = []
    for i, stock in enumerate(stocks[:20], 1):
        color = score_color(stock.composite_score)
        news_lines = ''
        if stock.top_news:
            item = stock.top_news[0]
            t = item['title']
            if len(t) > 45:
                cutoff = t[:45]
                last_space = cutoff.rfind(' ')
                remainder = t[last_space+1:last_space+16]
                t = cutoff[:last_space] + ' ' + remainder if last_space > 20 else t[:45]
                t += '...'
            if item.get('url'):
                news_lines = '<a href="' + item['url'] + '" target="_blank" rel="noopener noreferrer" style="color:#fff;text-decoration:none">' + t + '</a>'
            else:
                news_lines = '<span style="color:#fff">' + t + '</span>'
        days_color = '#ff4444' if stock.days_to_earnings == 0 else ('#ffcc00' if stock.days_to_earnings <= 7 else ('#58a6ff' if stock.days_to_earnings <= 15 else '#00ff88'))
        bg = 'rgba(0,255,136,0.12)' if round(stock.composite_score)>=80 else 'rgba(31,111,235,0.12)'
        #tbody = ''.join(rows_html)

    # Build full HTML
    SCANNER_TITLE = "AI Market Cap Scanner"
    html = '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>' + SCANNER_TITLE + '</title>'
    favicon_path = "file:///C:/Users/Tyler_AI/ai-market-cap/favicon.ico" if LOCAL_MODE else "/favicon.ico"
    html += '<link rel="icon" type="image/x-icon" href="' + favicon_path + '">'
    html += '<meta name="description" content="AI pre-earnings momentum scanner for tech stocks. Track scores, analyst ratings, PE targets, and implied moves before earnings reports.">'
    html += '<meta property="og:title" content="AI Market Cap Scanner">'
    html += '<meta property="og:description" content="Pre-Earnings Tech Stock Scanner for AI stocks. Scores, PE targets, and 14-day implied moves before earnings reports.">'
    html += '<meta property="og:image" content="https://aismarketcap.com/static/logo.png">'
    html += '<meta property="og:url" content="https://aismarketcap.com">'
    html += '<meta property="og:type" content="website">'
    html += '<meta name="twitter:card" content="summary_large_image">'
    html += '<meta name="twitter:title" content="AI Market Cap Scanner">'
    html += '<meta name="twitter:description" content="Pre-earnings momentum scanner for AI/tech stocks. Track scores, analyst ratings, PE targets, and implied moves before earnings.">'
    html += '<meta name="twitter:image" content="https://aismarketcap.com/static/logo.png">'
    html += '<style>'
    html += '*{margin:0;padding:0;box-sizing:border-box}body{font-family:Segoe UI,Arial,sans-serif;background:#0d1117;color:#c9d1d9;padding:0;margin:0}'
    html += '.header{background:linear-gradient(135deg,#1a1f2e,#161b22);padding:25px;border-radius:12px;margin-bottom:20px;border:1px solid #30363d}'
    html += '.hdr-row{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:15px}'
    html += 'h1{color:#fff;font-size:1.8em;margin-bottom:5px}.desc{color:#8b949e;font-size:0.95em}'
    html += '.btn{background:#ffd700;border:2px solid #fff;color:#000;padding:10px 22px;border-radius:6px;font-size:0.9em;cursor:pointer;font-weight:bold;flex-shrink:0;box-shadow:0 0 12px rgba(255,215,0,0.5)}.btn:hover{background:#2ea043}.btn:active{background:#238636}.btn:disabled{background:#444;cursor:not-allowed}#refreshBtn{background:#1f6feb;border:2px solid #fff;box-shadow:0 0 12px rgba(31,111,235,0.5)}#refreshBtn:hover{background:#388bfd}'
    
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
    html += 'th.sorted-asc::after{content:" â–²";color:#00ff88}'
    html += 'th.sorted-desc::after{content:" â–“";color:#00ff88}'
    html += 'td{padding:10px 10px;border-bottom:1px solid #30363d;font-size:0.88em;color:#fff}td:nth-child(6){border-right:2px solid #3fb950;box-shadow:1px 0 8px rgba(63,185,80,0.5)}tr{height:auto}tr:hover{background:#1c2128}'
    html += '.note{margin-top:20px;padding:12px 18px;background:#161b22;border-radius:8px;font-size:0.82em;color:#8b949e;border:1px solid #30363d}.earn-cell{font-size:0.82em}'
    html += '.disclaimer{margin-top:12px;padding:12px 18px;background:#1a1a1a;border-radius:8px;font-size:0.80em;color:#999;border:1px solid #c0392b}'
    html += ".pick-banner{background:linear-gradient(135deg,#2a1a00,#ffd700);border:2px solid #ffd700;border-radius:8px;padding:40px 18px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;min-height:120px}"
    html += '#chat-btn{position:fixed;bottom:24px;right:24px;background:#ffd700;color:#000;border:2px solid #000;border-radius:10px;padding:14px 28px;font-size:1.05em;font-weight:bold;cursor:pointer;box-shadow:0 0 12px rgba(255,215,0,0.5);z-index:9999}@keyframes feat-glow{0%,100%{box-shadow:0 0 8px rgba(255,215,0,.5)}50%{box-shadow:0 0 25px rgba(255,215,0,.9)}}@keyframes sb-glow{0%,100%{box-shadow:0 0 4px rgba(63,185,80,.3)}50%{box-shadow:0 0 10px rgba(63,185,80,.6)}}tr[style*="rgba(0,255,136,0.12)"]{animation:sb-glow 2.5s ease-in-out infinite;border-left:3px solid #3fb950}.pick-banner{animation:feat-glow 2s ease-in-out infinite}'
    html += '#chat-btn:hover{background:#e6c200}'
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
    html += "@media(max-width:768px){body{padding:0!important;background:#0d1117}.header{padding:14px 12px}.hdr-row{flex-direction:column;align-items:start;gap:10px}h1{font-size:1.4em}h1 a{font-size:1.4em}.desc{font-size:0.85em}.btn{padding:10px 16px;font-size:0.95em}#refreshBtn,#scanBtn{margin-top:4px}.stats-bar{flex-direction:column;gap:8px}.ticker-strip{font-size:0.8em;padding:8px 0}.pick-banner{flex-direction:column;gap:8px;padding:16px 12px;min-height:unset}.pick-banner span{font-size:0.95em!important}.stat{padding:8px 12px}.note,.disclaimer{padding:10px 12px;font-size:0.78em}#stockTable{overflow-x:auto;display:block;-webkit-overflow-scrolling:touch}#stockTable thead,#stockTable tbody,#stockTable tr,#stockTable th,#stockTable td{display:block}#stockTable thead tr{position:absolute;top:-9999px;left:-9999px}#stockTable tbody tr{border-bottom:1px solid #30363d;padding:10px 12px;display:flex;flex-wrap:wrap}#stockTable td{position:relative;padding:4px 8px!important;border:none!important;width:auto!important;min-width:50%}#stockTable td:first-child{width:100%!important;font-size:1.1em;font-weight:bold}#stockTable td:nth-child(2){width:100%!important;font-size:0.85em;color:#8b949e;margin-bottom:4px}#stockTable td::before{content:attr(data-label);position:absolute;top:4px;left:8px;font-size:0.7em;color:#6e7681;text-transform:uppercase;font-weight:bold}#stockTable td>strong,#stockTable td>a{font-size:1em!important}#stockTable td>br{display:none}.pick-banner strong{font-size:1.1em!important}#chat-panel{right:4px;bottom:60px;width:calc(100vw-8px);max-width:360px}#chat-btn{padding:12px 20px;font-size:1em}}"
    html += '#chat-input-row{display:flex;border-top:1px solid #30363d;padding:10px 12px;gap:8px}'
    html += '#chat-input{flex:1;background:#0d1117;border:1px solid #30363d;border-radius:8px;color:#c9d1d9;padding:8px 12px;font-size:0.88em;resize:none;outline:none;font-family:Segoe UI,Arial,sans-serif}'
    html += '#chat-input:focus{border-color:#58a6ff}'
    html += '#chat-send{background:#238636;border:none;color:#fff;border-radius:8px;padding:8px 16px;font-size:0.88em;cursor:pointer;font-weight:bold}#chat-send:hover{background:#2ea043}#chat-send:disabled{background:#444;cursor:not-allowed}#stockTableBody tr td:last-child{background:transparent;transition:background .15s}#stockTableBody tr td:last-child:hover{background:rgba(88,166,255,.18)}'
    html += '#sub-popup{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.75);display:none;align-items:center;justify-content:center;z-index:99999}#sub-popup.show{display:flex}#sub-popup-box{background:#161b22;border:2px solid #ffd700;border-radius:14px;padding:36px 32px;max-width:420px;width:90%;text-align:center;box-shadow:0 0 40px rgba(255,215,0,.3);animation:pop-in .4s ease}@keyframes pop-in{from{transform:scale(.7);opacity:0}to{transform:scale(1);opacity:1}}#sub-popup-box h2{color:#ffd700;font-size:1.4em;margin:0 0 8px}#sub-popup-box p{color:#c9d1d9;font-size:.95em;margin:0 0 20px;line-height:1.5}#sub-popup-features{display:flex;flex-direction:column;gap:8px;margin-bottom:22px;text-align:left}#sub-popup-features div{color:#fff;font-size:.88em;display:flex;align-items:center;gap:8px}#sub-popup-features div span{color:#00ff88;font-weight:bold}#sub-popup-btn{background:#ffd700;border:2px solid #000;color:#000;padding:12px 28px;border-radius:8px;font-size:1em;font-weight:bold;cursor:pointer;text-decoration:none;display:inline-block;margin-right:10px}#sub-popup-btn:hover{background:#e6c200}#sub-popup-close{background:#30363d;border:1px solid #30363d;color:#8b949e;padding:10px 20px;border-radius:8px;font-size:.88em;cursor:pointer}#sub-popup-close:hover{color:#fff}'
    html += '@media(max-width:600px){body{padding:0;font-size:13px}#stockTable{font-size:12px;width:100%!important;max-width:100%!important;margin:0!important;display:block;overflow-x:visible!important;-webkit-overflow-scrolling:touch}#stockTable thead,#stockTable tbody,#stockTable tr,#stockTable td,#stockTable th{display:block}#stockTable thead{position:absolute;top:-9999px;left:-9999px}#stockTable tr{border:1px solid #30363d;border-radius:0;margin:0;padding:8px;background:#161b22;border-top:none}#stockTable td{position:relative;padding:3px 8px;border:none;font-size:12px;line-height:1.4}#stockTable td:before{content:attr(data-label);font-weight:700;color:#58a6ff;margin-right:6px}#stockTable td.earn-cell{font-size:11px}#stockTable td a{font-size:13px!important}.header{margin:0;padding:12px 8px;background:#161b22;border-left:none;border-right:none}.hdr-row{flex-direction:column!important;gap:8px;padding:0!important;width:100%!important}.hdr-row>div{width:100%!important;max-width:100%!important;flex:unset!important}.ticker-strip{border-radius:0;margin:0;background:#161b22;border:1px solid #30363d;border-left:none;border-right:none;overflow:hidden}.note,.disclaimer{border:1px solid #30363d;border-radius:0;margin:0;border-left:none;border-right:none;padding:10px 8px!important;background:#161b22}}'
    html += '</style></head><body>'
    html += '<div id=sub-popup><div id=sub-popup-box><h2>Unlock Full Scanner Power</h2><p>Subscribe for 3 daily scans, real-time alerts, and the AI Chat Analyst.</p><div id=sub-popup-features><div><span>&#10003;</span> 3 daily scans</div><div><span>&#10003;</span> Real-time earnings alerts</div><div><span>&#10003;</span> AI Chat Analyst</div><div><span>&#10003;</span> Priority pre-earnings picks</div></div><a href="/pricing" id=sub-popup-btn>Subscribe Now</a><button id=sub-popup-close onclick="document.getElementById(\'sub-popup\').classList.remove(\'show\')">Maybe Later</button></div></div>'
    html += '<script>setTimeout(function(){document.getElementById("sub-popup").classList.add("show")},300000)</script>'

    # Ticker strip
    ticker_items = ''
    for s in stocks:
        if round(s.composite_score) < 50:
            continue
        chg = s.price_change_pct
        chg_cls = 'ticker-up' if chg >= 0 else 'ticker-dn'
        chg_str = f'+{chg:.2f}%' if chg >= 0 else f'{chg:.2f}%'
        ticker_items += f'<span class=ticker-item><span style="font-weight:bold;color:#00ff88">{round(s.composite_score)}</span> <span class=ticker-sym>{s.ticker}</span> <span class=ticker-price>${int(s.current_price)}</span> <span class="ticker-chg {chg_cls}">{chg_str}</span></span>'
    # Add Kraken referral as last strip item
    ticker_items += '<a href="https://invite.kraken.com/JDNW/dq0q352v" target="_blank" style="display:inline-flex;align-items:center;gap:6px;padding:0 18px;border-right:1px solid #30363d;flex-shrink:0;text-decoration:none"><span style="font-size:1em">&#x1F4B8;</span><span style="font-weight:bold;color:#00ff88;font-size:0.9em">$300 Sign Up Bonus</span><span style="font-weight:bold;color:#9333ea;font-size:0.9em">Trade On Kraken</span></a>'
    html += '<div class=ticker-strip><div class=ticker-strip-inner>' + ticker_items + ticker_items + '</div></div>'

    # IPO cards - centered middle column (auto-skips past IPOs based on date)
    all_ipos = [
        {'company': 'Applied Aerospace', 'date': datetime(2026, 6, 3), 'deal': '$634M', 'link': 'https://www.prnewswire.com/news-releases/applied-aerospace--defense-inc-announces-launch-of-initial-public-offering-302781752.html'},
        {'company': 'SpaceX', 'date': datetime(2026, 6, 12), 'deal': '$1.5T', 'link': 'https://www.spacex.com/ipo'},
        {'company': 'Discord', 'date': datetime(2026, 9, 1), 'deal': '$15B', 'link': 'https://discord.com/ipo'},
        {'company': 'Databricks', 'date': datetime(2026, 9, 15), 'deal': '$134B', 'link': 'https://www.databricks.com/company/corporate-overview/ipo'},
        {'company': 'OpenAI', 'date': datetime(2026, 12, 1), 'deal': '$1T', 'link': 'https://openai.com/enterprise'},
        {'company': 'Anthropic', 'date': datetime(2026, 10, 15), 'deal': '$380B', 'link': 'https://www.anthropic.com'},
    ]
    # Filter out past IPOs and sort by date
    today = datetime.now()
    upcoming = [ipo for ipo in all_ipos if ipo['date'] >= today]
    upcoming.sort(key=lambda x: x['date'])
    ipo_list = upcoming[:3]

    # Get DRAM ETF price
    try:
        import yfinance as yf
        dram = yf.Ticker("DRAM")
        dram_info = dram.fast_info
        dram_price = dram_info.get('last_price') or dram_info.get('previous_close')
        if not dram_price:
            hist = dram.history(period="1d")
            dram_price = hist['Close'].iloc[-1] if not hist.empty else None
        dram_price_str = f"${dram_price:.2f}" if dram_price else "$--"
    except:
        dram_price_str = "$--"
    # Buttons row
    buttons_row = (
        '<div style="display:flex;flex-direction:column;gap:6px;align-items:flex-end;flex-shrink:0">'
        '<div style="display:flex;gap:6px;align-items:center">'
        '<a href="/about" style="background:#dc3545;color:#fff;padding:10px 18px;border-radius:6px;font-size:0.9em;text-decoration:none;font-weight:bold;border:1px solid #fff" onmouseover="this.style.background=\'#e84a5f\'" onmouseout="this.style.background=\'#dc3545\'">FAQ</a>'
        '<a href="/wins" style="background:#238636;color:#fff;padding:10px 18px;border-radius:6px;font-size:0.9em;text-decoration:none;font-weight:bold;border:1px solid #fff" onmouseover="this.style.background=\'#2ea043\'" onmouseout="this.style.background=\'#238636\'">Wins</a>'
        '<a href="/calendar" style="background:#1f6feb;color:#fff;padding:10px 18px;border-radius:6px;font-size:0.9em;text-decoration:none;font-weight:bold;border:1px solid #fff" onmouseover="this.style.background=\'#388bfd\'" onmouseout="this.style.background=\'#1f6feb\'">Calendar</a>'
        '<button class=btn id=scanBtn style="background:#ffd700;color:#000;font-weight:bold;border:1px solid #fff;cursor:pointer" onmouseover="this.style.background=\'#fff176\'" onmouseout="this.style.background=\'#ffd700\'" onclick=runScan()>PRO SCAN</button>'
        '</div>'
        '<div style="display:flex;gap:6px;align-items:center">'
        '<a href="https://x.com/AIMoneyMach" target="_blank" style="background:#5741d9;color:#fff;padding:3px 10px;border-radius:5px;border:1px solid #fff;font-size:0.82em;font-weight:bold;text-decoration:none" onmouseover="this.style.background=\'#6e55e0\'" onmouseout="this.style.background=\'#5741d9\'">Follow Us On X</a>'
        '<span style="background:#161b22;border:1px solid #2ea043;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#2ea043">' + str(strong_count) + '</span> <span style="color:#8b949e">Strong Buy</span></span>'
        '<span style="background:#161b22;border:1px solid #1f6feb;border-radius:5px;padding:3px 10px;font-size:0.82em"><span style="font-weight:bold;color:#58a6ff">' + str(sum(1 for s in stocks if 50 <= round(s.composite_score) < 75)) + '</span> <span style="color:#8b949e">Watch</span></span>'
        '</div>'
        '</div>'
    )
    # Build IPO cards dynamically - filters past IPOs, always shows 5 upcoming
    ipo_card_html = '<div style="display:flex;gap:6px;align-items:center;justify-content:center;flex-wrap:wrap;max-width:800px;margin:0 auto">'
    styles = [
        ('#2ea043', 'SOONEST TOP IPO', 'rgba(46,160,67,0.3)'),
        ('#1f6feb', 'NEXT TOP IPO', 'rgba(31,111,235,0.3)'),
        ('#ffd700', 'TOP IPO', 'rgba(255,215,0,0.2)'),
    ]
    for i, ipo in enumerate(ipo_list):
        lbl_color, lbl_text, glow = styles[i] if i < len(styles) else styles[-1]
        date_str = ipo['date'].strftime('%b %d')
        company = ipo['company']
        deal = ipo.get('deal', '')
        link = ipo['link']
        ipo_card_html += (
            f'<div style="background:#0d1a0d;border:1px solid {lbl_color};border-radius:8px;padding:8px 14px;min-width:140px;box-shadow:0 0 10px {glow}">'
            f'<div style="color:{lbl_color};font-size:0.65em;font-weight:bold;margin-bottom:2px">&#128293; {lbl_text}</div>'
            f'<a href="{link}" target="_blank" style="color:#00ff88;font-size:0.95em;font-weight:bold;text-decoration:none">{company}</a>'
            f'<div style="color:#fff;font-size:0.68em">{date_str} | {deal}</div></div>'
        )
    # Add DRAM card in purple (in same row, with gap)
    ipo_card_html += (
        f'<div style="background:#0d1428;border:1px solid #5741d9;border-radius:8px;padding:8px 14px;min-width:140px;box-shadow:0 0 10px rgba(87,65,217,0.3);margin-left:24px">'
        f'<div style="color:#9333ea;font-size:0.65em;font-weight:bold;margin-bottom:2px">&#128293; TRENDING ETF</div>'
        f'<a href="https://finance.yahoo.com/quote/DRAM/" target="_blank" style="color:#00ff88;font-size:0.95em;font-weight:bold;text-decoration:none">DRAM</a>'
        f'<div style="color:#fff;font-size:0.68em">{dram_price_str}</div></div>'
    )
    ipo_card_html += '</div>'
    html += '<div class=header><div class=hdr-row>'
    html += '<div><a href="https://aismarketcap.com" style="color:#fff;text-decoration:none"><h1>' + SCANNER_TITLE + '</h1></a><div style="color:#fff;font-size:0.95em">Pre-Earnings Tech Stock Scanner</div></div>'
    html += ipo_card_html
    html += buttons_row
    html += '</div></div>'
    html += '<div class=warn id=warnMsg></div>'

    if pick:
        html += '<div class=pick-banner style="background:#161b22;border:2px solid #2ea043;border-radius:10px;padding:40px 18px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:15px 0;min-height:120px;box-shadow:0 0 20px rgba(46,160,67,0.4)">'
        html += '<span style="font-size:1.3em;color:#2ea043;font-weight:bold">&#9733; AI\'s Suggested Trade</span>'
        html += '<span style="font-size:1.2em;font-weight:bold;color:#fff">' + pick.ticker + '</span>'
        html += '<span style="font-size:0.95em;color:#fff">' + pick.company_name[:28] + ('...' if len(pick.company_name) > 28 else '') + '</span>'
        html += '<span style="font-size:0.95em;color:#fff">Score: <strong style="color:' + pick_color + '">' + str(round(pick.composite_score)) + '</strong></span>'
        html += '<span style="font-size:0.95em;color:#fff">Buy Price: <strong style="color:#00ff88">$' + str(int(pick.current_price)) + '</strong></span>'
        pick_earn_label = 'Today' if pick.days_to_earnings == 0 else str(pick.days_to_earnings)
        html += '<span style="font-size:1em;color:#00ff88;font-weight:bold">Enter now - ' + pick_earn_label + ' days to earnings</span>'
        html += '<a href="https://invite.kraken.com/JDNW/dq0q352v" target="_blank" style="display:inline-block;background:#5741d9;color:#fff;padding:8px 18px;border-radius:6px;font-weight:bold;text-decoration:none;font-size:0.9em;margin-left:auto">Trade ' + pick.ticker + ' on Kraken</a>'
        html += '</div>'

    if pick2:
        html += '<div class=pick-banner style="background:#161b22;border:2px solid #1f6feb;border-radius:10px;padding:40px 18px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:0 0 15px;min-height:120px;box-shadow:0 0 20px rgba(31,111,235,0.4)">'
        html += '<span style="font-size:1.3em;color:#58a6ff;font-weight:bold">&#9733; Runner-Up Pick</span>'
        html += '<span style="font-size:1.2em;font-weight:bold;color:#fff">' + pick2.ticker + '</span>'
        html += '<span style="font-size:0.95em;color:#fff">' + pick2.company_name[:28] + ('...' if len(pick2.company_name) > 28 else '') + '</span>'
        html += '<span style="font-size:0.95em;color:#fff">Score: <strong style="color:' + pick2_color + '">' + str(round(pick2.composite_score)) + '</strong></span>'
        html += '<span style="font-size:0.95em;color:#fff">Buy Price: <strong style="color:#58a6ff">$' + str(int(pick2.current_price)) + '</strong></span>'
        pick2_earn_label = 'Today' if pick2.days_to_earnings == 0 else str(pick2.days_to_earnings)
        html += '<span style="font-size:1em;color:#58a6ff;font-weight:bold">Enter now - ' + pick2_earn_label + ' days to earnings</span>'
        html += '<a href="https://invite.kraken.com/JDNW/dq0q352v" target="_blank" style="display:inline-block;background:#5741d9;color:#fff;padding:8px 18px;border-radius:6px;font-weight:bold;text-decoration:none;font-size:0.9em;margin-left:auto">Trade ' + pick2.ticker + ' on Kraken</a>'
        html += '</div>'

    headers = [
        ('Ticker<br>Symbol','ticker'), ('Company<br>Name','company_name'), ('Overall<br>Score','score'),
        ('Earnings<br>Date','earnings_date'), ('Days<br>Left','days_left'), ('Current<br>Price','price'),
        ('3 Day<br>Target','pe_target'), ('7 Day<br>Target','3d'), ('14 Day<br>Target','5d'),
        ('Total<br>Analyst','analysts'), ('Strong<br>Buy','sb'), ('Buy<br>Ratings','buy'),
        ('Hold<br>Ratings','hold'), ('Sell<br>Ratings','sell'), ('Market<br>Cap','mktcap'),
        ('Total<br>Shorts','short_int'), ('Implied<br>Volatility','iv'),
        ('Earnings<br>Trend','sentiment'), ('Recent News','news')
    ]
    ths = ''
    col_labels = {
        'ticker': 'Ticker', 'company_name': 'Company', 'score': 'Score',
        'earnings_date': 'Earnings', 'days_left': 'Days', 'price': 'Price',
        'pe_target': '3 Day', '3d': '7 Day', '5d': '14 Day',
        'analysts': 'Analysts', 'sb': 'Strong Buy', 'buy': 'Buy',
        'hold': 'Hold', 'sell': 'Sell', 'mktcap': 'Mkt Cap',
        'short_int': 'Shorts', 'iv': 'IV', 'sentiment': 'Trend', 'news': 'News'
    }
    for h, col in headers:
        label = col_labels.get(col, col)
        ths += '<th onclick="sortBy(\'' + col + '\')" data-col="' + col + '" data-label="' + label + '">' + h + '</th>'
    html += '<table id="stockTable"><thead><tr>' + ths + '</tr></thead><tbody id="stockTableBody">'

    rows_data = []
    count = 0
    for stock in stocks[:30]:
        if stock.composite_score < 50:
            continue
        count += 1
        rows_data.append({
            'rank': count, 'ticker': stock.ticker, 'company_name': stock.company_name,
            'score': round(stock.composite_score), 'earnings_date': fmt_date(stock.earnings_date),
            'days_left': stock.days_to_earnings, 'price': round(stock.current_price, 2),
            'pe_target': round(stock.post_earnings_target, 2), 'pe_upside': round(stock.post_earnings_upside_pct, 1),
            '3d': round(stock.post_earnings_3d_target, 2), '3d_up': round(stock.post_earnings_3d_upside_pct, 1),
            '5d': round(stock.post_earnings_5d_target, 2), '5d_up': round(stock.post_earnings_5d_upside_pct, 1),
            'analysts': stock.total_analysts, 'sb': stock.strong_buy_rating,
            'buy': stock.buy_rating, 'hold': stock.hold_rating, 'sell': stock.sell_rating,
            'mktcap': stock.market_cap,
            'short_int': round(stock.short_interest, 1) if stock.short_interest else 0,
            'iv': round(stock.implied_volatility, 1) if stock.implied_volatility else 0,
            'sector': stock.sector or 'Technology',
            'sentiment': stock.earnings_sentiment,
            'news': stock.top_news[0] if stock.top_news else None
        })

    import json
    # Build static table rows in Python - no JS needed for display
    def score_color_css(score):
        return '#00ff88' if score >= 75 else '#58a6ff'
    def row_bg(score):
        return 'rgba(0,255,136,0.12)' if score >= 75 else 'rgba(31,111,235,0.12)'
    def days_color(days):
        return '#ff4444' if days == 0 else ('#ffcc00' if days <= 7 else ('#58a6ff' if days <= 15 else '#00ff88'))
    def news_link(news):
        if not news:
            return '--'
        url = news.get('url', '')
        title = news.get('title', '')
        # Cut at 45 chars but include the next complete word so sentences make sense, add ...
        if len(title) > 45:
            cutoff = title[:45]
            last_space = cutoff.rfind(' ')
            remainder = title[last_space+1:last_space+16]
            title = cutoff[:last_space] + ' ' + remainder if last_space > 20 else title[:45]
            title += '...'
        if url:
            return '<a href="' + url + '" target="_blank" style="color:#fff;text-decoration:none">' + title + '</a>'
        return '<span style="color:#fff">' + title + '</span>'
    def fmt_mktcap(val):
        if val >= 1000:
            return str(int(round(val / 1000))) + ' T'
        elif val >= 1:
            return str(int(round(val))) + ' B'
        else:
            return str(int(round(val * 1000))) + ' M'

    static_rows = ''
    for r in rows_data:
        c_color = score_color_css(r['score'])
        bg_color = row_bg(r['score'])
        d_color = days_color(r['days_left'])
        co_name = r['company_name'][:35] + ('...' if len(r['company_name']) > 35 else '')
        news_cell = news_link(r['news'])
        static_rows += '<tr style="background:' + bg_color + '">'
        static_rows += '<td data-label="Ticker"><strong><a href="https://finance.yahoo.com/quote/' + r['ticker'] + '" target="_blank" style="color:#66b2ff">' + r['ticker'] + '</a></strong></td>'
        static_rows += '<td data-label="Company">' + co_name + '</td>'
        static_rows += '<td data-label="Score"><strong style="color:' + c_color + '">' + str(r['score']) + '</strong></td>'
        static_rows += '<td data-label="Earnings">' + r['earnings_date'] + '</td>'
        days_str = 'Today' if r['days_left'] == 0 else str(r['days_left']) + 'd'
        static_rows += '<td data-label="Days"><span style="color:' + d_color + ';font-weight:bold">' + days_str + '</span></td>'
        static_rows += '<td data-label="Price" style="font-weight:bold">$' + str(int(r['price'])) + '</td>'
        static_rows += '<td data-label="3 Day"><span style="font-weight:bold">$' + str(int(r['pe_target'])) + '</span><br><span style="color:#00ff88">+' + str(r['pe_upside']) + '%</span></td>'
        static_rows += '<td data-label="7 Day">$' + str(int(r['3d'])) + '<br><span style="color:#00ff88">+' + str(r['3d_up']) + '%</span></td>'
        static_rows += '<td data-label="14 Day">$' + str(int(r['5d'])) + '<br><span style="color:#00ff88">+' + str(r['5d_up']) + '%</span></td>'
        static_rows += '<td data-label="Analysts" style="color:#bf8fff">' + str(r['analysts']) + '</td>'
        static_rows += '<td data-label="Strong Buy" style="color:#00ff88">' + str(r['sb']) + '</td>'
        static_rows += '<td data-label="Buy" style="color:#58a6ff">' + str(r['buy']) + '</td>'
        static_rows += '<td data-label="Hold" style="color:#ffcc00">' + str(r['hold']) + '</td>'
        static_rows += '<td data-label="Sell" style="color:#ff6b6b">' + str(r['sell']) + '</td>'
        static_rows += '<td data-label="Mkt Cap">' + fmt_mktcap(r['mktcap']) + '</td>'
        static_rows += '<td data-label="Shorts" style="color:#fff">' + str(r['short_int']) + '%</td>'
        static_rows += '<td data-label="IV" style="color:#fff">' + str(r['iv']) + '%</td>'
        sent = r.get('sentiment', '')
        if sent == 'Positive':
            sent_badge = '<span style="background:#1a2a1a;border:1px solid #2ea043;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#00ff88">' + sent + '</span>'
        elif sent == 'Negative':
            sent_badge = '<span style="background:#2a1a1a;border:1px solid #ff4444;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#ff6b6b">' + sent + '</span>'
        elif sent == 'Mixed':
            sent_badge = '<span style="background:#2a2a1a;border:1px solid #ffd700;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#ffd700">' + sent + '</span>'
        else:
            sent_badge = 'â€"'
        static_rows += '<td data-label="Trend">' + sent_badge + '</td>'
        static_rows += '<td data-label="News">' + news_cell + '</td>'
        static_rows += '</tr>'

    html += static_rows + '</tbody></table>'
    html += '<script>var rowsData=' + json.dumps(rows_data) + ';\n'
    html += "var sortCol='score';var sortAsc=false;function getVal(r,col){var m={'ticker':r.ticker,'company_name':r.company_name,'score':r.score,'earnings_date':r.earnings_date,'days_left':r.days_left,'price':r.price,'pe_target':r.pe_target,'3d':r['3d'],'5d':r['5d'],'analysts':r.analysts,'sb':r.sb,'buy':r.buy,'hold':r.hold,'sell':r.sell,'mktcap':r.mktcap,'short_int':r.short_int,'iv':r.iv,'sentiment':r.sentiment};return m[col]||r[col]||0;}function updateArrows(){document.querySelectorAll('th[data-col]').forEach(function(th){th.classList.remove('sorted-asc','sorted-desc');});var th=document.querySelector('th[data-col=\"'+sortCol+'\"]');if(th){th.classList.add(sortAsc?'sorted-asc':'sorted-desc');}}function sortBy(col){if(sortCol===col){sortAsc=!sortAsc;}else{sortCol=col;sortAsc=col==='score'||col==='analysts'||col==='sb'||col==='buy'||col==='hold'||col==='sell'||col==='price'||col==='pe_target'||col==='3d'||col==='5d'||col==='mktcap'||col==='short_int'||col==='iv';}var dirs={'ticker':1,'company_name':1};var asc=dirs[col]?sortAsc:!sortAsc;rowsData.sort(function(a,b){var va=getVal(a,col),vb=getVal(b,col);if(typeof va==='number')return asc?va-vb:vb-va;return asc?String(va).localeCompare(String(vb)):String(vb).localeCompare(String(va));});renderTable();updateArrows();}function fmtMktcap(v){if(v>=1000)return Math.round(v/1000)+' T';if(v>=1)return Math.round(v)+' B';return Math.round(v*1000)+' M';}function scoreColor(s){return s>=80?'#00ff88':'#58a6ff';}function newsHtml(n){if(!n)return'';var u=n.url||'';var t=n.title||'';if(t.length>45){var sp=t.lastIndexOf(' ',45);var rm=sp>0?t.substring(sp+1,sp+16):'';t=sp>20?t.substring(0,sp)+' '+rm:t.substring(0,45);t+='...';}return u?'<a href=\"'+u+'\" target=\"_blank\" style=\"color:#fff;text-decoration:none\">'+t+'</a>':'<span style=\"color:#fff\">'+t+'</span>';}function renderTable(){var tbody=document.getElementById('stockTableBody');if(!tbody)return;var html='';rowsData.forEach(function(r){if(r.score<50)return;var c=scoreColor(r.score);var bg=r.score>=80?'rgba(0,255,136,0.12)':'rgba(31,111,235,0.12)';html+='<tr style=\"background:'+bg+'\"><td><strong><a href=\"https://finance.yahoo.com/quote/'+r.ticker+'\" target=\"_blank\" style=\"color:#66b2ff\">'+r.ticker+'</a></strong></td>';html+='<td>'+r.company_name.substring(0,35)+(r.company_name.length>35?'...':'')+'</td>';html+='<td><strong style=\"color:'+c+';font-size:1.3em\">'+r.score+'</strong></td>';html+='<td class=earn-cell>'+r.earnings_date.replace(chr(10),'<br>')+'</td>';html+='<td style=\"color:'+(r.days_left==0?'#ff4444':(r.days_left<=7?'#00ff88':'#ffcc00'))+';font-weight:bold\">'+(r.days_left==0?'Today':r.days_left+'d')+'</td>';html+='<td>$'+Math.floor(r.price)+'</td>';html+='<td>$'+Math.floor(r.pe_target)+' | +'+r.pe_upside+'%</td>';html+='<td>$'+Math.floor(r['3d'])+' | +'+r['3d_up']+'%</td>';html+='<td>$'+Math.floor(r['5d'])+' | +'+r['5d_up']+'%</td>';html+='<td>'+r.analysts+'</td>';html+='<td style=\"color:#00ff88\">'+r.sb+'</td>';html+='<td style=\"color:#58a6ff\">'+r.buy+'</td>';html+='<td style=\"color:#ffcc00\">'+r.hold+'</td>';html+='<td style=\"color:#ff6b6b\">'+r.sell+'</td>';html+='<td>'+fmtMktcap(r.mktcap)+'</td>';html+='<td style=\'color:#fff\'>'+r.short_int+'%</td>';html+='<td style=\'color:#fff\'>'+r.iv+'%</td>';html+='<td>'+(r.squeeze?'<span style=\'background:#1a2a1a;border:1px solid #2ea043;border-radius:5px;padding:2px 8px;font-size:0.75em;font-weight:bold;color:#00ff88\'>Yes</span>':'â€”')+'</td>';html+='<td>'+newsHtml(r.news)+'</td></tr>';});tbody.innerHTML=html;};sortBy('days_left');"

    html += '</script>'
    html += '<div class=note><b>Scoring:</b> Analyst Coverage (25pts linear) + Buy% Conviction (25pts) + Strong Buy Count (2pts each, max 20) + 5D Upside (max 15pts) + Earnings Sentiment (max 15pts) | <b>PE Target:</b> straddle x1 (Conservative Target) | <b>3-Day Momentum:</b> straddle x3 (Mid Target) | <b>5-Day Momentum:</b> straddle x5 (High Target) | <b>Entry:</b> 1-30 days pre-earnings | <b>Exit:</b> 1-5 days after earnings beat</div>'
    html += '<div class=disclaimer>&#9888; <b>Not a financial advisor.</b> This scanner is for informational purposes only. Options data and targets are estimates based on ATM straddles -- actual results may vary. Stocks carry risk; always do your own research before trading. AisMarketCap.com is not liable for any losses incurred from trades based on this data.</div>'
    html += "<script>var scanBtn=document.getElementById('scanBtn');var warnMsg=document.getElementById('warnMsg');function runScan(){scanBtn.disabled=true;warnMsg.textContent='Starting scan...';var x=new XMLHttpRequest();x.open('POST','/run',true);x.onload=function(){if(x.responseURL&&x.responseURL.endsWith('/pricing')){scanBtn.disabled=false;window.location.href='/pricing';return;}warnMsg.textContent='Scan started! Reloading...';location.reload(true);};x.onerror=function(){scanBtn.disabled=false;warnMsg.textContent='Error - try again.';setTimeout(function(){warnMsg.style.display='none';},4000);};x.send();}function refreshData(){location.reload(true);}</script>"

    # Chat widget - clean plain JS, no HTML entities
    html += '<button id="chat-btn" onclick="toggleChat()">Ask AI</button>'
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
    html += "fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:m})}).then(function(r){if(r.redirected||r.url.includes('/pricing')){window.location.href='/pricing';return Promise.reject('redirect');}return r.json();}).then(function(d){"
    html += 'loadingDiv.remove();'
    html += 'var botDiv=document.createElement("div");'
    html += 'botDiv.className="msg msg-bot";'
    html += 'botDiv.textContent=d.reply||"Got it.";'
    html += 'ms.appendChild(botDiv);'
    html += 'ms.scrollTop=ms.scrollHeight;'
    html += '}).catch(function(e){'
    html += 'if(e==="redirect")return;'
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
    'CRDO': datetime(2026, 6, 1).date(),  # Finviz: Jun 01 AMC
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--days', type=int, default=45, help='Days ahead to scan (1-45)')
    parser.add_argument('--top', type=int, default=20)
    parser.add_argument('--local', action='store_true', help='Use local desktop paths (favicon, etc.)')
    args = parser.parse_args()
    LOCAL_MODE = args.local
    print("AI Earnings Scanner - Pre-Earnings Momentum (1-30 Day Window)"); print("="*55)
    if not YF_AVAILABLE: print("ERROR: yfinance not installed. Run: python -m pip install yfinance"); sys.exit(1)

    # Generate favicon from logo (crop icon + resize)
    logo_src = os.path.join(os.path.expanduser("~"), "Desktop", "logo.png")
    favicon_dst = os.path.join(os.path.dirname(os.path.abspath(__file__)), "favicon.ico")
    if os.path.exists(logo_src):
        try:
            from PIL import Image
            img = Image.open(logo_src)
            cropped = img.crop((0, 0, img.width, int(img.height * 0.72)))
            favicon_ico = cropped.resize((32, 32), Image.LANCZOS)
            favicon_ico.save(favicon_dst, format='ICO', sizes=[(16,16),(32,32),(48,48)])
            print("Favicon generated")
        except Exception as e:
            print(f"Favicon generation skipped: {e}")

    # Fetch dynamic AI stock list from finviz + hardcoded AI-niche tickers (merged)
    print("Fetching AI stocks from finviz screener...")
    finviz_tickers = fetch_ai_stocks_from_finviz()
    # Always include hardcoded AI_TICKERS (ensures CRDO and other niche AI plays are scanned)
    all_tickers = list(dict.fromkeys(finviz_tickers + AI_TICKERS))  # deduped, finviz first
    print(f"Total stocks to scan: {len(all_tickers)} (finviz:{len(finviz_tickers)} + hardcoded:{len(AI_TICKERS)})")

    # First scan to get all earnings in window with real dates
    all_results = []
    today = datetime.now().date()
    failed_tickers = []
    for i, ticker in enumerate(all_tickers):
        if ticker in EXCLUDED_TICKERS: continue
        # Rate-limit: small pause every 20 tickers to avoid overwhelming yfinance
        if i > 0 and i % 20 == 0:
            _time.sleep(0.5)
        try:
            if ticker in EARNINGS_OVERRIDES:
                edate = EARNINGS_OVERRIDES[ticker]
                days_out = (edate - today).days
                if 0 <= days_out <= args.days:
                    all_results.append((ticker, edate, days_out))
            else:
                cal = get_earnings_with_retry(ticker)
                if cal and 'Earnings Date' in cal:
                    ed = cal['Earnings Date']
                    if isinstance(ed, list) and ed:
                        edate = ed[0]
                        if hasattr(edate, 'date'): edate = edate.date()
                        days_out = (edate - today).days
                if 0 <= days_out <= args.days:
                            all_results.append((ticker, edate, days_out))
                else:
                    failed_tickers.append(ticker)
        except Exception as e:
            failed_tickers.append(ticker)

    if failed_tickers:
        print(f"  [INFO] yfinance failed for {len(failed_tickers)} tickers: {', '.join(failed_tickers[:20])}")
    all_results.sort(key=lambda x: x[2])
    print(f"Found {len(all_results)} AI stocks with earnings in next {args.days} days:")

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

    # === SAVE PICK TRACKER ===
    # Track AI pick and runner-up with entry prices for win tracking
    strong_buys = [s for s in stocks if round(s.composite_score) >= 75]
    strong_buys.sort(key=lambda x: -x.days_to_earnings)
    pick_data = []
    today_str = datetime.now().strftime('%Y-%m-%d')
    for s in strong_buys[:5]:
        pick_data.append({
            'date': today_str,
            'ticker': s.ticker,
            'price': round(s.current_price, 2),
            'score': round(s.composite_score),
            'days_left': s.days_to_earnings,
            'company': s.company_name,
            'pe_target': round(s.post_earnings_target, 2) if s.post_earnings_target else 0,
            '5d_target': round(s.post_earnings_5d_target, 2) if s.post_earnings_5d_target else 0
        })
    tracker_path = os.path.join(os.path.dirname(__file__) or '.', 'pick_tracker.json')
    import json as _json
    with open(tracker_path, 'w') as f:
        _json.dump(pick_data, f, indent=2)
    print(f"[Pick Tracker] saved {len(pick_data)} picks to pick_tracker.json")

    timestamp = datetime.now().strftime('%Y%m%d_%H%M'); out_dir = os.path.dirname(__file__) or '.'
    html_path = os.path.join(out_dir, f'ai_earnings_57day_{timestamp}.html')
    csv_path = os.path.join(out_dir, f'ai_earnings_57day_{timestamp}.csv')
    today_path = os.path.join(out_dir, 'ai_earnings_today.html')
    print(f"Generating HTML report...")
    generate_html_report(stocks[:args.top], html_path)
    # Also save as ai_earnings_today.html so the web server can serve it directly
    generate_html_report(stocks[:args.top], today_path)
    print(f"Generating CSV report...")
    generate_csv_report(stocks, csv_path)

    # Self-validate: ensure rowsData is complete
    with open(today_path, 'r', encoding='utf-8') as f:
        content = f.read()
    idx = content.find('var rowsData=')
    if idx >= 0:
        arr_depth, json_end = 0, idx
        for i in range(idx + 12, len(content)):
            ch = content[i]
            if ch == '[': arr_depth += 1
            elif ch == ']':
                arr_depth -= 1
                if arr_depth == 0:
                    json_end = i
                    break
        json_len = json_end - (idx + 12) + 1
        print(f"[Validate] rowsData = {json_len} bytes")
        if json_len < 5000:
            print(f"[Validate] WARNING: rowsData too short ({json_len} bytes). Check scan output.")
        else:
            print(f"[Validate] rowsData OK ({len(stocks[:args.top])} stocks)")

    print("Done!")


if __name__ == '__main__': main()
