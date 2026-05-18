"""Lightweight background price updater — runs every 5 minutes.
Only updates prices in the latest scan HTML. Does NOT affect the scan logic.
Run with: python live_prices.py (starts in background)
Stop with: python live_prices.py --stop"""
import sys, time, re
from pathlib import Path

WORKSPACE = Path(__file__).parent
REFRESH_INTERVAL = 300  # 5 minutes
STOP_FILE = Path(__file__).parent / "live_prices_stop.txt"

def get_latest_scan():
    files = sorted(WORKSPACE.glob("ai_earnings_57day_*.html"), key=lambda f: f.stat().st_mtime, reverse=True)
    return files[0] if files else None

def fetch_prices(tickers):
    prices = {}
    try:
        import yfinance as yf
        for ticker in tickers:
            try:
                t = yf.Ticker(ticker)
                info = t.info
                price = info.get('currentPrice') or info.get('regularMarketPrice')
                prev = info.get('previousClose') or info.get('regularMarketPreviousClose')
                if price:
                    chg_pct = 0.0
                    chg_abs = 0.0
                    if prev and prev > 0:
                        chg_abs = round(price - prev, 2)
                        chg_pct = round((chg_abs / prev) * 100, 2)
                    prices[ticker] = {'price': round(price, 2), 'chg_pct': chg_pct, 'chg_abs': chg_abs}
                    print(f"  {ticker}: ${round(price,2)} ({'+' if chg_pct >= 0 else ''}{chg_pct}%)")
            except Exception as e:
                print(f"  {ticker}: error - {e}")
    except ImportError:
        print("yfinance not available — price update skipped")
    return prices

def update_html(scan_file, prices):
    with open(scan_file, 'r', encoding='utf-8') as f:
        html = f.read()

    updated = False

    # Update ticker strip
    if prices:
        ticker_items = ''
        # Extract existing tickers from ticker strip (from table order)
        table_tickers = re.findall(r'<td[^>]*><strong><a[^>]*>([A-Z]+)</a>', html)
        if not table_tickers:
            # fallback: extract all ticker symbols from table
            table_tickers = re.findall(r'<a href="https://finance\.yahoo\.com/quote/([A-Z]+)"', html)
        # Deduplicate while preserving order
        seen = set()
        unique_tickers = []
        for t in table_tickers:
            if t not in seen:
                seen.add(t)
                unique_tickers.append(t)

        for ticker in unique_tickers:
            if ticker in prices:
                p = prices[ticker]
                chg_str = f'+{p["chg_pct"]:.2f}%' if p['chg_pct'] >= 0 else f'{p["chg_pct"]:.2f}%'
                chg_cls = 'ticker-up' if p['chg_pct'] >= 0 else 'ticker-dn'
                ticker_items += f'<span class=ticker-item><span class=ticker-sym>{ticker}</span> <span class=ticker-price>${p["price"]}</span> <span class="ticker-chg {chg_cls}">{chg_str}</span></span>'
            else:
                ticker_items += f'<span class=ticker-item><span class=ticker-sym>{ticker}</span> <span class=ticker-price>--</span> <span class="ticker-chg ticker-up">--</span></span>'

        # Replace the ticker strip inner content
        old_strip = re.search(r'<div class=ticker-strip-inner>(.*?)</div></div>', html)
        if old_strip and ticker_items:
            new_strip = f'<div class=ticker-strip-inner>{ticker_items}{ticker_items}</div></div>'
            html = html[:old_strip.start()] + new_strip + html[old_strip.end():]
            updated = True

    # Update price cells in the table (find $PRICE in each row)
    if prices:
        for ticker, p in prices.items():
            # Find the price cell for this ticker — pattern: ticker link followed by company, then score, then date info, then price
            # Price appears after: days-left td + price td
            ticker_pattern = r'<a href="https://finance\.yahoo\.com/quote/' + ticker + r'"[^>]*>[^<]*</a></strong></td>\s*<td>[^<]*</td>\s*<td[^>]*>[^<]*</td>\s*<td[^>]*>([^<]+)</td>\s*<td[^>]*>([^<]+)</td>\s*<td[^>]*>(\$[\d]+\.[\d]{2})</td>'
            def replace_price(m):
                days = m.group(1); date = m.group(2); old_price = m.group(3)
                return m.group(0).replace(old_price, f'${p["price"]}')
            html, count = re.subn(ticker_pattern, replace_price, html)
            if count > 0:
                updated = True

    if updated:
        ts = time.strftime('%Y-%m-%d %H:%M')
        html = re.sub(r'Updated: [^|]+ \|', f'Updated: {ts} |', html, count=1)
        with open(scan_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"[Live Prices] Updated {scan_file.name} at {ts}")
    else:
        print(f"[Live Prices] No updates needed")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--stop':
        STOP_FILE.write_text('stop')
        print("Stop signal sent — daemon will stop after next cycle")
        return

    print(f"[Live Prices] Starting background price updater (every {REFRESH_INTERVAL}s)")
    print("[Live Prices] To stop: python live_prices.py --stop")

    while True:
        if STOP_FILE.exists():
            print("[Live Prices] Stop signal received — shutting down")
            STOP_FILE.unlink(missing_ok=True)
            break

        try:
            scan_file = get_latest_scan()
            if scan_file:
                # Extract tickers from the scan
                tickers = re.findall(r'<a href="https://finance\.yahoo\.com/quote/([A-Z]+)"', scan_file.read_text(encoding='utf-8'))
                tickers = list(dict.fromkeys(tickers))  # preserve order, remove dupes
                print(f"[Live Prices] Fetching {len(tickers)} prices: {tickers}")
                prices = fetch_prices(tickers)
                if prices:
                    update_html(scan_file, prices)
            else:
                print("[Live Prices] No scan file found — waiting...")
        except Exception as e:
            print(f"[Live Prices] Error: {e}")

        # Sleep in chunks so stop signal is checked every 30s
        for _ in range(REFRESH_INTERVAL // 30):
            if STOP_FILE.exists():
                print("[Live Prices] Stop signal received — shutting down")
                STOP_FILE.unlink(missing_ok=True)
                sys.exit(0)
            time.sleep(30)

if __name__ == '__main__':
    main()