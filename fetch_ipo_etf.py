"""Fetch real upcoming IPOs and top trending ETF each day.

- IPOs: scraped from stockanalysis.com IPO calendar
- Trending ETF: ranked by 5-day momentum from a curated AI/tech ETF list
Saves to ipo_etf_data.json — consumed by ai_earnings_scanner.py.
"""
import json, re, time, logging, sys
from pathlib import Path
from datetime import datetime, timedelta

import requests
import yfinance as yf

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s',
                    datefmt='%H:%M:%S')
log = logging.getLogger('ipo_etf')

SCRIPT_DIR = Path(__file__).parent
OUTPUT_FILE = SCRIPT_DIR / 'ipo_etf_data.json'
REQUEST_TIMEOUT = 15
MAX_RETRIES = 2

# ─── IPO SCRAPING ────────────────────────────────────────────────────────────

def _svelte_to_json(s: str) -> str:
    """Convert Svelte unquoted-key JS object format to valid JSON.

    Svelte serializes data as: {s:"IAM",n:"Iambic"}
    Standard JSON needs:          {"s":"IAM","n":"Iambic"}
    """
    # Quote unquoted keys (bare word before colon, after { or ,)
    s = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', s)
    # Remove trailing commas before } or ]
    s = re.sub(r',(\s*[}\]])', r'\1', s)
    return s


def scrape_ipos() -> list[dict]:
    """Scrape upcoming IPOs from stockanalysis.com IPO calendar.

    Returns up to 5 upcoming IPOs with: company, ticker, date, price_range, deal_size.
    """
    url = 'https://stockanalysis.com/ipos/calendar/'
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, timeout=REQUEST_TIMEOUT,
                                headers={
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                                                  'Chrome/120.0.0.0 Safari/537.36',
                                })
            resp.raise_for_status()
            html = resp.text
            break
        except Exception as e:
            log.warning(f'IPO scrape attempt {attempt+1} failed: {e}')
            if attempt == MAX_RETRIES - 1:
                return []
            time.sleep(3)
            continue

    ipos = []

    # Find thisWeekData:[...] directly in the HTML
    # Svelte embeds it as: thisWeekData:[{s:"IAM",...}]
    raw = re.search(r'thisWeekData:\[(.*?)\](?=,)', html, re.DOTALL)
    if raw:
        arr_str = '[' + raw.group(1) + ']'
        try:
            rows = json.loads(_svelte_to_json(arr_str))
            today = datetime.now()
            for row in rows:
                name = (row.get('n') or '').strip()
                ticker = (row.get('s') or '').strip()
                date_str = (row.get('ipoDate') or '').strip()
                price_range = (row.get('ipoPriceRange') or '').strip()
                deal_size = row.get('ds') or 0

                if not name or len(name) < 3 or not ticker:
                    continue
                # Skip long tickers (ETF/unit tickers often are longer or all-caps)
                if len(ticker) > 5:
                    continue

                try:
                    ipo_date = datetime.strptime(date_str, '%Y-%m-%d')
                except (ValueError, TypeError):
                    continue

                if ipo_date < today - timedelta(hours=12):
                    continue

                if deal_size >= 1_000_000_000:
                    deal_str = f'${deal_size / 1_000_000_000:.0f}B'
                elif deal_size >= 1_000_000:
                    deal_str = f'${deal_size / 1_000_000:.0f}M'
                else:
                    deal_str = price_range if price_range else 'TBD'

                link = f'https://stockanalysis.com/stocks/{ticker.lower()}/' if ticker else ''

                ipos.append({
                    'company': name,
                    'ticker': ticker,
                    'date': ipo_date.strftime('%b %d'),
                    'date_full': ipo_date.strftime('%Y-%m-%d'),
                    'price_range': price_range,
                    'deal': deal_str,
                    'link': link,
                })
                log.info(f'  IPO: {ticker} {name} {ipo_date.strftime("%b %d")} {deal_str}')
                if len(ipos) >= 5:
                    break
        except (json.JSONDecodeError, Exception) as e:
            log.warning(f'IPO parse error: {e}')

    if not ipos:
        log.warning('No IPOs scraped from stockanalysis.com - using fallback watchlist')
        # Fallback: high-profile expected/filed IPOs (TBD dates, used when scrape is empty)
        # Updated periodically; these are companies that have filed S-1 or are widely expected
        ipos = [
            {'company': 'Stripe', 'ticker': 'STRIPE', 'date': 'TBD', 'date_full': '',
             'price_range': 'TBD', 'deal': '~$10B+', 'link': 'https://stockanalysis.com/stocks/strp/'},
            {'company': 'Databricks', 'ticker': 'DBRX', 'date': 'TBD', 'date_full': '',
             'price_range': 'TBD', 'deal': '~$60B', 'link': 'https://stockanalysis.com/stocks/dbrx/'},
            {'company': 'Canva', 'ticker': 'CNVA', 'date': 'TBD', 'date_full': '',
             'price_range': 'TBD', 'deal': '~$40B', 'link': 'https://stockanalysis.com/stocks/cnva/'},
            {'company': 'SpaceX', 'ticker': 'SPACE', 'date': 'TBD', 'date_full': '',
             'price_range': 'TBD', 'deal': '~$400B', 'link': 'https://stockanalysis.com/stocks/space/'},
            {'company': 'OpenAI', 'ticker': 'OPAI', 'date': 'TBD', 'date_full': '',
             'price_range': 'TBD', 'deal': '~$500B', 'link': 'https://stockanalysis.com/stocks/opai/'},
        ]
        for ipo in ipos:
            log.info(f'  IPO (fallback): {ipo["ticker"]} {ipo["company"]} {ipo["deal"]}')

    return ipos


# ─── TRENDING ETF ───────────────────────────────────────────────────────────

AI_TECH_ETFS = [
    ('ARKK',    'ARK Innovation ETF'),
    ('SOXX',    'iShares Semiconductor ETF'),
    ('SMH',     'VanEck Semiconductor ETF'),
    ('XSD',     'SPDR S&P Semiconductor ETF'),
    ('IGV',     'iShares Expanded Tech-Software Sector ETF'),
    ('SKYY',    'First Trust Cloud Computing ETF'),
    ('BOTZ',    'Global X Robotics & AI ETF'),
    ('AIQ',     'Global X Artificial Intelligence & Tech ETF'),
    ('CIBR',    'First Trust NASDAQ Cybersecurity ETF'),
    ('HACK',    'ETFMG Prime Cyber Security ETF'),
    ('FINX',    'Global X FinTech ETF'),
    ('BUG',     'Global X Cybersecurity ETF'),
    ('NERD',    'Roundhill Video Game Tech ETF'),
    ('SOCL',    'Global X Social Media ETF'),
    ('WCLD',    'Citigroup US Cloud Leaders ETF'),
    ('DTEC',    'ALPS Disruptive Technologies ETF'),
    ('HERO',    'Global X Video Games & Tech ETF'),
]

def fetch_trending_etf() -> dict:
    """Return the top AI/tech ETF by 5-day price momentum.

    Downloads 5-day history for each ETF and picks the one with the
    highest % return. Returns dict with ticker, name, price, change_5d.
    """
    results = []
    tickers = [t for t, _ in AI_TECH_ETFS]

    # Batch download in one yfinance call (faster)
    try:
        data = yf.download(tickers, period='7d', progress=False, threads=True, group_by='ticker')
    except Exception as e:
        log.warning(f'ETF batch download failed: {e}')
        return fallback_trending_etf()

    for ticker, name in AI_TECH_ETFS:
        try:
            ticker_upper = ticker.upper()
            if ticker_upper in data.columns.get_level_values(0):
                closes = data[ticker_upper]['Close'].dropna()
            else:
                # Fallback: single ticker download
                t = yf.Ticker(ticker)
                hist = t.history(period='7d')
                closes = hist['Close']

            if closes.empty or len(closes) < 2:
                continue

            price = round(float(closes.iloc[-1]), 2)
            change_5d = round(((closes.iloc[-1] - closes.iloc[0]) / closes.iloc[0]) * 100, 2)

            results.append({
                'ticker': ticker.upper(),
                'name': name,
                'price': price,
                'change_5d': change_5d,
            })
        except Exception as e:
            log.debug(f'ETF {ticker} skipped: {e}')
            continue

    if not results:
        log.warning('No ETF data fetched — using fallback')
        return fallback_trending_etf()

    # Sort by 5-day momentum, highest first
    results.sort(key=lambda x: x['change_5d'], reverse=True)
    winner = results[0]

    log.info(f'Trending ETF: {winner["ticker"]} {winner["name"]} '
             f'${winner["price"]} ({winner["change_5d"]:+.2f}% 5d)')

    # Return top 3 for logging/debugging
    for r in results[:3]:
        log.info(f'  ETF {r["ticker"]}: {r["change_5d"]:+.2f}% 5d @ ${r["price"]}')

    return winner


def fallback_trending_etf() -> dict:
    """Return DRAM as a safe fallback."""
    try:
        dram = yf.Ticker('DRAM')
        hist = dram.history(period='1d')
        price = round(float(hist['Close'].iloc[-1]), 2) if not hist.empty else 0
        return {'ticker': 'DRAM', 'name': 'Exchange Listed: DRAM ETF',
                'price': price, 'change_5d': 0}
    except Exception:
        return {'ticker': 'DRAM', 'name': 'DRAM ETF', 'price': 0, 'change_5d': 0}


# ─── MAIN ────────────────────────────────────────────────────────────────────

def run() -> dict:
    """Fetch IPOs and trending ETF. Saves to ipo_etf_data.json. Returns the data dict."""
    log.info('Fetching IPO calendar...')
    ipos = scrape_ipos()

    log.info('Fetching trending ETF...')
    trending_etf = fetch_trending_etf()

    data = {
        'fetched_at': datetime.now().isoformat(),
        'ipos': ipos,
        'trending_etf': trending_etf,
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)

    log.info(f'Saved to {OUTPUT_FILE} — {len(ipos)} IPOs, trending ETF: {trending_etf["ticker"]}')
    return data


if __name__ == '__main__':
    run()
