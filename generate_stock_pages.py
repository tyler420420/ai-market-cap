"""
Stock Pages Generator — builds SEO-optimized static pages for each ticker.
aismarketcap.com/stock/NOW, /stock/CRWD, etc.
Target: "TICKER stock earnings [month] [year]" long-tail queries.

Run: python generate_stock_pages.py
Pages saved to: stock_pages/ directory (git-tracked, Railway serves statically)
"""
import os, sys, json, re, argparse, requests
from pathlib import Path
from datetime import datetime, timedelta
import yfinance as yf

# Get the scanner tickers
SCANNER = Path(__file__).parent / "ai_earnings_scanner.py"
OUTPUT_DIR = Path(__file__).parent / "stock_pages"

def get_tickers():
    """Extract tickers from ai_earnings_scanner.py AI_TICKERS list."""
    content = SCANNER.read_text(encoding="utf-8")
    # Find the start of AI_TICKERS list and extract ALL tickers until EXCLUDED_TICKERS
    start = content.find('AI_TICKERS = [')
    end = content.find('EXCLUDED_TICKERS', start)
    if start == -1 or end == -1:
        return []
    block = content[start:end]
    tickers = re.findall(r"'([A-Z]+)'", block)
    return list(dict.fromkeys(tickers))  # dedupe preserving order

def get_stock_data(ticker):
    """Fetch live data for a ticker using yfinance."""
    try:
        t = yf.Ticker(ticker)
        info = t.info or {}
        cal = None
        try:
            cal = t.calendar
        except Exception:
            pass

        # Earnings date
        earnings_date = None
        days_to_earnings = None
        if cal and 'Earnings Date' in cal:
            ed = cal['Earnings Date']
            if isinstance(ed, list) and ed:
                earnings_date = ed[0].strftime('%B %d, %Y') if hasattr(ed[0], 'strftime') else str(ed[0])
                days_to_earnings = (ed[0] - datetime.now()).days if hasattr(ed[0], 'days') else None
            elif isinstance(ed, (list, tuple)) and ed[0]:
                earnings_date = str(ed[0])
        if not earnings_date:
            # Fallback: next earnings from info
            earnings_date = info.get('earningsDates', None)
            if isinstance(earnings_date, list) and earnings_date:
                earnings_date = str(earnings_date[0])

        return {
            'ticker': ticker,
            'name': info.get('shortName', '') or info.get('longName', '') or ticker,
            'price': info.get('currentPrice') or info.get('regularMarketPrice') or 0,
            'mktcap': info.get('marketCap', 0),
            'pe': info.get('trailingPE', 0),
            'fwd_pe': info.get('forwardPE', 0),
            'eps': info.get('trailingEps', 0),
            'revenue': info.get('totalRevenue', 0),
            'analyst_count': info.get('numberOfAnalystOpinions', 0),
            'target_price': info.get('targetMeanPrice', 0),
            'sector': info.get('sector', ''),
            'industry': info.get('industry', ''),
            'earnings_date': earnings_date,
            'days_to_earnings': days_to_earnings,
            'rec_buy': info.get('recommendationKey', '') in ('buy', 'strong_buy', 'moderate_buy'),
            'rec_label': info.get('recommendationKey', 'N/A'),
            'sector': info.get('sector', ''),
            'industry': info.get('industry', ''),
        }
    except Exception as e:
        return {
            'ticker': ticker,
            'name': ticker,
            'price': 0,
            'mktcap': 0,
            'pe': 0,
            'earnings_date': None,
            'days_to_earnings': None,
            'error': str(e)[:80],
        }

def format_currency(val):
    if not val: return 'N/A'
    if val >= 1_000_000_000_000: return f"${val/1_000_000_000_000:.1f}T"
    if val >= 1_000_000_000: return f"${val/1_000_000_000:.1f}B"
    if val >= 1_000_000: return f"${val/1_000_000:.0f}M"
    return f"${val:.0f}"

def build_page(d):
    ticker = d['ticker']
    name = d['name']
    price = d['price']
    mktcap = d['mktcap']
    pe = d['pe']
    sector = d.get('sector', '')
    industry = d.get('industry', '')
    earnings_date = d.get('earnings_date') or 'Upcoming'
    days = d.get('days_to_earnings')
    analyst_count = d.get('analyst_count', 0)
    target = d.get('target_price', 0)
    rec = d.get('rec_label', 'N/A')
    eps = d.get('eps', 0)

    month = datetime.now().strftime('%B %Y')
    next_month = (datetime.now().replace(day=28) + timedelta(days=4)).strftime('%B %Y')

    # Build earnings status
    if days is not None and days >= 0:
        if days == 0:
            earn_label = f"{name} ({ticker}) Reports Earnings Today — {earnings_date}"
            earn_status = f"Reports <strong>TODAY</strong> · {earnings_date}"
        elif days == 1:
            earn_label = f"{name} ({ticker}) Earnings Tomorrow — {earnings_date}"
            earn_status = f"Reports <strong>TOMORROW</strong> · {earnings_date}"
        elif days <= 7:
            earn_label = f"{name} ({ticker}) Earnings This Week — {earnings_date}"
            earn_status = f"Earns in <strong>{days} days</strong> · {earnings_date}"
        elif days <= 30:
            earn_label = f"{name} ({ticker}) Earnings {earnings_date}"
            earn_status = f"Earns in <strong>{days} days</strong> · {earnings_date}"
        else:
            earn_label = f"{name} ({ticker}) Stock Analysis — {earnings_date}"
            earn_status = f"Next earnings: <strong>{earnings_date}</strong>"
    else:
        earn_label = f"{name} ({ticker}) Stock Analysis — {earnings_date}"
        earn_status = f"Next earnings: <strong>{earnings_date}</strong>"

    meta_desc = (
        f"{name} ({ticker}) stock analysis. "
        f"{earn_status.replace('<strong>', '').replace('</strong>', '')}. "
        f"Pre-earnings momentum scanner, analyst ratings, PE targets, and entry signals. "
        f"Updated daily for {month}."
    )

    price_str = f"${price:.2f}" if price else "N/A"
    mktcap_str = format_currency(mktcap)
    pe_str = f"{pe:.1f}" if pe else "N/A"
    target_str = f"${target:.0f}" if target else "N/A"
    eps_str = f"${eps:.2f}" if eps else "N/A"

    rec_color = '#2ea043' if rec in ('buy', 'strong_buy', 'moderate_buy') else '#ffa657' if rec == 'hold' else '#f85149'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{earn_label}</title>
<meta name="description" content="{meta_desc}">
<meta property="og:title" content="{earn_label}">
<meta property="og:description" content="{meta_desc}">
<meta property="og:type" content="article">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://aismarketcap.com/stock/{ticker}">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #0d1117; color: #c9d1d9; line-height: 1.6; }}
  a {{ color: #58a6ff; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .topbar {{ background: linear-gradient(135deg,#1a1f2e,#161b22); padding: 20px 24px; border-bottom: 1px solid #30363d; display: flex; align-items: center; gap: 20px; flex-wrap: wrap; }}
  .topbar-brand {{ color: #7ee787; font-size: 1.2em; font-weight: bold; }}
  .topbar-brand span {{ color: #ffd700; }}
  .topbar a {{ color: #8b949e; font-size: 0.85em; }}
  .topbar a:hover {{ color: #fff; }}
  .container {{ max-width: 860px; margin: 0 auto; padding: 28px 20px; }}
  .breadcrumb {{ font-size: 0.78em; color: #444; margin-bottom: 20px; }}
  .breadcrumb a {{ color: #58a6ff; }}
  h1 {{ color: #fff; font-size: 1.8em; margin-bottom: 6px; }}
  .subtitle {{ color: #8b949e; font-size: 0.9em; margin-bottom: 20px; }}
  .earn-badge {{ display: inline-block; background: rgba(255,215,0,0.15); border: 1px solid #ffd700; color: #ffd700; padding: 5px 14px; border-radius: 20px; font-size: 0.82em; font-weight: bold; margin-bottom: 20px; }}
  .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin-bottom: 28px; }}
  .metric {{ background: #161b22; border: 1px solid #21262d; border-radius: 10px; padding: 16px; text-align: center; }}
  .metric .val {{ font-size: 1.4em; font-weight: bold; color: #7ee787; }}
  .metric .lbl {{ font-size: 0.7em; color: #555; text-transform: uppercase; margin-top: 3px; }}
  .section {{ background: #161b22; border: 1px solid #21262d; border-radius: 12px; padding: 22px; margin-bottom: 18px; }}
  .section h2 {{ color: #fff; font-size: 1em; margin-bottom: 14px; font-weight: 600; border-bottom: 1px solid #21262d; padding-bottom: 10px; }}
  .section p {{ color: #8b949e; font-size: 0.88em; margin-bottom: 10px; }}
  .section ul {{ color: #8b949e; font-size: 0.88em; padding-left: 20px; margin-bottom: 10px; }}
  .section li {{ margin-bottom: 6px; }}
  .highlight {{ color: #fff; font-weight: 600; }}
  .green {{ color: #7ee787; }}
  .amber {{ color: #ffa657; }}
  .blue {{ color: #58a6ff; }}
  .cta {{ background: linear-gradient(135deg,#1a2a1a,#0d1a0d); border: 2px solid #2ea043; border-radius: 12px; padding: 24px; text-align: center; margin-bottom: 18px; }}
  .cta h2 {{ color: #7ee787; border: none; padding: 0; margin-bottom: 8px; }}
  .cta p {{ color: #8b949e; font-size: 0.88em; margin-bottom: 16px; }}
  .cta-btn {{ display: inline-block; background: #ffd700; color: #000; padding: 12px 28px; border-radius: 8px; font-weight: bold; font-size: 0.9em; text-decoration: none; }}
  .cta-btn:hover {{ background: #ffe033; text-decoration: none; }}
  .scanner-link {{ text-align: center; margin: 10px 0 24px; font-size: 0.82em; color: #444; }}
  .scanner-link a {{ color: #58a6ff; }}
  .tag {{ display: inline-block; background: #1f2937; color: #9ca3af; padding: 2px 10px; border-radius: 4px; font-size: 0.75em; margin: 2px; }}
  .footer {{ text-align: center; color: #333; font-size: 0.75em; padding: 30px 20px; border-top: 1px solid #1e1e2e; margin-top: 20px; }}
  .footer a {{ color: #444; }}
</style>
</head>
<body>

<div class="topbar">
  <div class="topbar-brand">AI Market Cap <span>Pro</span></div>
  <div>
    <a href="https://aismarketcap.com">← Back to Scanner</a>
    <a href="https://aismarketcap.com/pricing">Pricing</a>
  </div>
</div>

<div class="container">
  <div class="breadcrumb">
    <a href="https://aismarketcap.com">Home</a> &rsaquo;
    <a href="https://aismarketcap.com/stocks">Stock Analysis</a> &rsaquo;
    <span>{ticker}</span>
  </div>

  <div class="earn-badge">📅 {earn_status}</div>

  <h1>{name} ({ticker}) — Pre-Earnings Stock Analysis</h1>
  <p class="subtitle">{sector}{', ' + industry if industry and sector else industry or ''}</p>

  <div class="metrics">
    <div class="metric">
      <div class="val">{price_str}</div>
      <div class="lbl">Current Price</div>
    </div>
    <div class="metric">
      <div class="val">{mktcap_str}</div>
      <div class="lbl">Market Cap</div>
    </div>
    <div class="metric">
      <div class="val">{pe_str}</div>
      <div class="lbl">Trailing P/E</div>
    </div>
    <div class="metric">
      <div class="val">{target_str}</div>
      <div class="lbl">Analyst Target</div>
    </div>
    <div class="metric">
      <div class="val">{analyst_count}</div>
      <div class="lbl">Analysts</div>
    </div>
    <div class="metric">
      <div class="val" style="color:{rec_color}">{rec.replace('_',' ').title() if rec else 'N/A'}</div>
      <div class="lbl">Rating</div>
    </div>
  </div>

  <div class="cta">
    <h2>🔥 Get {ticker} Targets Before Earnings</h2>
    <p>Pre-earnings entry zone, analyst PE target, 3-day and 5-day implied move, and stop loss — all unlocked with a $5/month subscription.</p>
    <a href="https://aismarketcap.com/pricing" class="cta-btn">Unlock Full Analysis →</a>
  </div>

  <div class="section">
    <h2>About {name} ({ticker})</h2>
    <p><span class="highlight">{name}</span> trades on NASDAQ under the ticker <span class="blue">{ticker}</span>. The company operates in the <span class="highlight">{sector or 'Technology'}</span> sector{sector and industry and f' — specifically <span class="highlight">{industry}</span>' or ''}.</p>
    <p>Current analyst consensus rating: <span style="color:{rec_color};font-weight:bold">{rec.replace('_',' ').title() if rec else 'N/A'}</span>{" with a $" + f"{target:.0f}" + " price target" if target else ""} based on {analyst_count} analyst {"opinion" if analyst_count == 1 else "opinions"}.</p>
    <p>EPS (trailing): <span class="green">{eps_str}</span> &nbsp;|&nbsp; Market Cap: <span class="green">{mktcap_str}</span></p>
    <p style="margin-top:12px">{" ".join([f'<span class="tag">{s.strip()}</span>' for s in [sector, industry] if s][:4]) if sector or industry else ''}</p>
  </div>

  <div class="section">
    <h2>Pre-Earnings Trading Strategy for {ticker}</h2>
    <p>Trading stocks before earnings requires understanding three key variables: the <span class="highlight">implied move</span> (what the options market expects), the <span class="highlight">historical beat rate</span> for the sector, and the <span class="highlight">current momentum</span> leading into the report.</p>
    <p>For {ticker}, the next earnings report is scheduled for <span class="highlight">{earnings_date}</span>.{" " + f" That's approximately {days} trading days away." if days and days >= 0 else ""}</p>
    <p>The implied move is calculated using at-the-money straddles — if the straddle is priced at X%, the market is pricing in approximately a ±X% move in either direction around the earnings release.</p>
    <ul>
      <li><strong>Buy before earnings</strong> when the implied move is <span class="amber">lower than historical actual moves</span> — the options are cheap relative to what the stock has historically done.</li>
      <li><strong>Set a stop loss</strong> at 10% below entry for pre-earnings positions — earnings volatility can swing 20-30% on a miss.</li>
      <li><strong>Sell within 5 days of a beat</strong> — momentum after a positive earnings surprise typically fades within a week as short-term traders take profits.</li>
      <li><strong>Check short interest</strong> — high short interest ({"above 15%" if mktcap and mktcap < 10_000_000_000 else "elevated"}) increases squeeze potential on a beat.</li>
    </ul>
  </div>

  <div class="section">
    <h2>How AI Market Cap Finds Pre-Earnings Setups</h2>
    <p>Our <a href="https://aismarketcap.com">pre-earnings momentum scanner</a> scores {ticker} across five factors to identify high-conviction setups:</p>
    <ul>
      <li><strong>Analyst conviction</strong> — {"Strong Buy ratings from " + str(analyst_count) + " analysts" if analyst_count else "Limited analyst coverage"} driving price targets above current market price.</li>
      <li><strong>Implied volatility rank</strong> — Whether options premiums are attractively priced relative to historical volatility.</li>
      <li><strong>Pre-earnings momentum</strong> — Whether the stock has been trending in the direction of the expected beat.</li>
      <li><strong>Sector sentiment</strong> — How the broader {sector or 'tech'} sector is positioned heading into this earnings cycle.</li>
      <li><strong>Days to earnings</strong> — The sweet spot is <span class="green">5-12 days before</span> — enough time for momentum to develop, not enough time for premium decay to hurt.</li>
    </ul>
    <p>The <a href="https://aismarketcap.com/pricing">Pro subscription</a> shows the full target range, stop loss, and implied move for {ticker} and all 20+ stocks in the current earnings window.</p>
  </div>

  <div class="scanner-link">
    See all stocks with earnings in the next 30 days →
    <a href="https://aismarketcap.com">AI Market Cap Pre-Earnings Scanner</a>
  </div>

</div>

<div class="footer">
  <a href="https://aismarketcap.com">AI Market Cap</a> &nbsp;|&nbsp;
  <a href="https://aismarketcap.com/privacy">Privacy</a> &nbsp;|&nbsp;
  Not financial advice. Always do your own research.<br>
  © {datetime.now().year} AI Market Cap
</div>

</body>
</html>"""

def ping_search_engines(sitemap_url):
    """Ping Google and Bing to crawl the sitemap after new pages are added."""
    results = {}
    # Google — free, no API key needed
    google_url = f"https://www.google.com/ping?sitemap={sitemap_url}"
    try:
        r = requests.get(google_url, timeout=15, headers={"User-Agent": "Mozilla/5.0 (compatible; AIScannerBot/1.0)"})
        ok = r.status_code == 200
        results["google"] = ok
        print(f"  {'✅' if ok else '⚠️'} Google sitemap ping: {r.status_code}")
    except Exception as e:
        results["google"] = False
        print(f"  ⚠️  Google sitemap ping failed: {e}")
    # Bing — free, no API key needed
    bing_url = f"https://www.bing.com/ping?sitemap={sitemap_url}"
    try:
        r = requests.get(bing_url, timeout=15, headers={"User-Agent": "Mozilla/5.0 (compatible; AIScannerBot/1.0)"})
        ok = r.status_code in [200, 201, 202]
        results["bing"] = ok
        print(f"  {'✅' if ok else '⚠️'} Bing sitemap ping: {r.status_code}")
    except Exception as e:
        results["bing"] = False
        print(f"  ⚠️  Bing sitemap ping failed: {e}")
    return results

def main():
    parser = argparse.ArgumentParser(description="AI Earnings Stock Page Generator")
    parser.add_argument("--ping", action="store_true", help="Ping Google + Bing sitemaps after generation")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True)
    tickers = get_tickers()
    print(f"Generating {len(tickers)} stock pages...")

    results = {'ok': 0, 'skip': 0, 'fail': 0}

    for i, ticker in enumerate(tickers, 1):
        out_file = OUTPUT_DIR / f"{ticker}.html"
        # Skip if already exists and file is recent (within 24h)
        # ALWAYS generate if the page doesn't exist yet — catches new scanner tickers
        if out_file.exists():
            age_h = (datetime.now() - datetime.fromtimestamp(out_file.stat().st_mtime)).total_seconds() / 3600
            if age_h < 24:
                results['skip'] += 1
                continue

        print(f"  [{i}/{len(tickers)}] {ticker}...", end=' ')
        d = get_stock_data(ticker)
        html = build_page(d)
        out_file.write_text(html, encoding='utf-8')
        if d.get('error'):
            print(f"ERR: {d['error']}")
            results['fail'] += 1
        else:
            print(f"OK — ${d.get('price', 'N/A')}")
            results['ok'] += 1

    print(f"\nDone: {results['ok']} pages generated, {results['skip']} skipped (fresh), {results['fail']} errors")

    if args.ping and results['ok'] > 0:
        print("\nPinging search engines for indexing...")
        ping_search_engines("https://aismarketcap.com/sitemap.xml")

if __name__ == '__main__':
    main()
