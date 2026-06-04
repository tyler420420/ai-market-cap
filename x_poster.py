"""
X/Twitter Posting Engine for AI Market Cap Scanner
Posts top 5 picks daily + fires winning trade alerts when PE targets are hit (every 4 hrs).
Uses direct HTTP calls to Twitter v2 API — no tweepy dependency.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
import os, json, time, re, datetime, sys
from pathlib import Path
from datetime import timezone, timedelta
import requests

# ===== CREDENTIALS (use env vars in production, fall back to hardcoded for Railway) =====
X_API_KEY = os.environ.get("X_API_KEY", "ptD4IFlECfhYAYiCIS2ueJcNb")
X_API_SECRET = os.environ.get("X_API_KEY_SECRET", "zZL8q7mClA75UPCtgiWLbrqrUaNXsOkVzTlhsQDD8ImnVskCsK")
X_ACCESS_TOKEN = os.environ.get("X_ACCESS_TOKEN", "2034074541757222912-GrzIxt79lOdpbxSYsc1XUfpXpFwC4o")
X_ACCESS_SECRET = os.environ.get("X_ACCESS_TOKEN_SECRET", "qRXpfp30a5LU2nqvbYT4FZj73SQxjTJHgrt6CjzuTIt5m")

PT = timezone(timedelta(hours=-7))
SCAN_FILE = Path(__file__).parent / "ai_earnings_today.html"
STATE_FILE = Path(__file__).parent / "twitter_alert_state.json"
TWEET_COOLDOWN_HOURS = 3
SITE_URL = "https://aismarketcap.com"

# ===== TWITTER API (v2, OAuth 1.0a via requests-oauthlib) =====
from requests_oauthlib import OAuth1

_twitter_auth = None

def get_twitter_auth():
    global _twitter_auth
    if _twitter_auth is None:
        _twitter_auth = OAuth1(
            client_key=X_API_KEY,
            client_secret=X_API_SECRET,
            resource_owner_key=X_ACCESS_TOKEN,
            resource_owner_secret=X_ACCESS_SECRET,
        )
    return _twitter_auth


def post_tweet(text):
    """Post a tweet. Returns tweet ID or None."""
    url = 'https://api.twitter.com/2/tweets'
    payload = json.dumps({'text': text})

    try:
        resp = requests.post(
            url,
            json={'text': text},
            auth=get_twitter_auth(),
            timeout=30
        )
        if resp.status_code == 201:
            tweet_id = resp.json().get('data', {}).get('id', 'unknown')
            print(f"[X] Posted tweet {tweet_id}: {text[:80]}...")
            return tweet_id
        elif resp.status_code == 429:
            print(f"[X] Rate limited. Response: {resp.text[:200]}")
            return None
        else:
            print(f"[X] Post failed {resp.status_code}: {resp.text[:200]}")
            return None
    except Exception as e:
        print(f"[X] Post error: {e}")
        return None


# ===== SCAN DATA =====
def load_latest_scan():
    """Load stocks from latest scan HTML file."""
    if not SCAN_FILE.exists():
        print("[X] No scan file found")
        return []

    content = SCAN_FILE.read_text(encoding='utf-8')
    idx = content.find('var rowsData=')
    if idx < 0:
        print("[X] No rowsData found")
        return []

    arr_depth, json_end = 0, idx
    for i in range(idx + 12, len(content)):
        ch = content[i]
        if ch == '[':
            arr_depth += 1
        elif ch == ']':
            arr_depth -= 1
            if arr_depth == 0:
                json_end = i
                break

    json_str = content[idx + 13:json_end + 1]
    clean = re.sub(r'<br\s*/?>', ' ', json_str)
    try:
        return json.loads(clean)
    except Exception as e:
        print(f"[X] JSON parse error: {e}")
        return []


# ===== STATE =====
def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except:
            pass
    return {'saved_picks': {}, 'tweeted_targets': {}, 'pick_history': []}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state))


# ===== TWEET CONTENT GENERATORS =====
def format_top5_tweet(stocks):
    """Post top 5 Strong Buy picks with price -> target format.
    Example:
    Daily Top Strong Buy Targets - http://aismarketcap.com
    1. ADSK 89 | $237 -> $256 (+8%)
    ...
    #AIStocks #StockMarket #Nasdaq #OptionsTrading #Trading #Investing
    """
    strong = [s for s in stocks if s.get('score', 0) >= 75]
    if not strong:
        print("[X] No Strong Buy picks to post")
        return False

    # Sort by highest score, tiebreaker by most days left (for main pick in tweet)
    top5 = sorted(strong, key=lambda x: (-x.get('score', 0), -x.get('days_left', 0)))[:5]

    lines = ["Daily Top Strong Buy Targets - " + SITE_URL, ""]

    for i, s in enumerate(top5, 1):
        ticker = s.get('ticker', '?')
        score = s.get('score', 0)
        price = s.get('price', 0)
        pe_target = s.get('pe_target', 0)
        pe_upside = s.get('pe_upside', 0)
        price_val = round(s.get('price', 0))
        target_val = round(s.get('pe_target', 0))
        upside_val = round(s.get('pe_upside', 0))
        lines.append(f"{i}. {ticker} {score} | ${price_val} -> ${target_val} (+{upside_val}%)")

    lines.append("")
    lines.append("#StockMarket #OptionsTrading #DayTrading #Investing #AIStocks")

    msg = '\n'.join(lines)
    if len(msg) > 280:
        msg = msg[:277] + "..."

    return post_tweet(msg)


def format_target_hit_tweet(ticker, name, current, target, gain_pct):
    """Tweet when a PE target is hit."""
    lines = [
        f"TARGET HIT! {ticker}",
        f"${round(current)} -> ${round(target)} (+{round(gain_pct)}%)",
        f"Track top AI picks: {SITE_URL}",
        "#StockMarket #OptionsTrading #DayTrading #Investing #AIStocks"
    ]
    msg = '\n'.join(lines)
    if len(msg) > 280:
        msg = msg[:277] + "..."
    return post_tweet(msg)


def post_win_tweet(win_url, ticker, entry_price, sell_target, gain_pct, days=1):
    """Post when a winning trade is confirmed. Call this after creating a win page."""
    lines = [
        f"Win! ✅ ${ticker.upper()} hit target in {days} days",
        "",
        f"Bought at ${round(entry_price)} -> Sold at ${round(sell_target)} (+{round(gain_pct)}%)",
        "",
        f"AI Market Cap called it. See the trade: {win_url}",
        "",
        "#AIStocks #WinningTrade #OptionsTrading #Investing"
    ]
    msg = '\n'.join(lines)
    if len(msg) > 280:
        msg = msg[:277] + "..."
    tweet_id = post_tweet(msg)
    if tweet_id:
        print(f"[X] Win tweet posted for {ticker}")
    return tweet_id


# ===== PRICE ALERTS =====
def get_current_price(ticker):
    """Get live price via yfinance."""
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        info = stock.fast_info
        price = info.get('last_price') or info.get('previous_close')
        return price
    except Exception as e:
        print(f"[X] Price fetch error for {ticker}: {e}")
        return None


def check_price_alerts(state):
    """Check if any picks from the last 3 days have hit their PE targets."""
    now = datetime.datetime.now(PT)
    three_days_ago = now - datetime.timedelta(days=3)

    # Build list of all picks from current + history (last 3 days)
    all_picks = []

    # Current saved_picks (from today's scan)
    for ticker, pick in state.get('saved_picks', {}).items():
        saved_at_str = pick.get('saved_at', '')
        if saved_at_str:
            try:
                saved_at = datetime.datetime.fromisoformat(saved_at_str)
                if saved_at >= three_days_ago:
                    all_picks.append((ticker, pick))
            except:
                pass

    # Pick history (from previous days)
    for day_picks in state.get('pick_history', []):
        for ticker, pick in day_picks.get('picks', {}).items():
            saved_at_str = pick.get('saved_at', '')
            if saved_at_str:
                try:
                    saved_at = datetime.datetime.fromisoformat(saved_at_str)
                    if saved_at >= three_days_ago:
                        all_picks.append((ticker, pick))
                except:
                    pass

    if not all_picks:
        print("[X] No picks from last 3 days to check")
        return []

    tweets = []

    for ticker, pick in all_picks:
        pe_target = pick.get('pe_target', 0)
        buy_price = pick.get('entry_price', 0)

        # Skip if no valid target
        if not pe_target or not buy_price or pe_target <= 0:
            continue

        # Check cooldown — one tweet per ticker, ever (permanent lock)
        last_tweet = state.get('tweeted_targets', {}).get(ticker)
        if last_tweet:
            continue  # Already fired for this ticker, skip forever

        current = get_current_price(ticker)
        if not current:
            continue

        gain_pct = ((current - buy_price) / buy_price) * 100 if buy_price > 0 else 0

        print(f"[X] {ticker}: ${current:.2f} | Target: ${pe_target:.2f} | Gain: {gain_pct:.1f}%")

        if current >= pe_target:
            # PE target hit — winning trade!
            tweet_id = format_target_hit_tweet(
                ticker, pick.get('name', ''), current, pe_target, gain_pct
            )
            if tweet_id:
                state['tweeted_targets'][ticker] = now.isoformat()
                tweets.append(('target_hit', ticker))
                print(f"[X] TARGET HIT! {ticker} posted")

    return tweets


# ===== POST SCAN (called by scanner_web.py /cron endpoint) =====
def post_daily_scan_to_twitter():
    """Post top 5 picks after a scan run. Called from scanner_web.py."""
    print("[X] Posting daily scan to Twitter...")
    state = load_state()
    stocks = load_latest_scan()

    if not stocks:
        print("[X] No stocks found in scan")
        return False

    # Filter to strong buys (score >= 86)
    strong = [s for s in stocks if s.get('score', 0) >= 86]
    if not strong:
        print("[X] No Strong Buy picks in scan")
        return False

    now = datetime.datetime.now(PT)

    # Archive current picks to history (keep last 3 days)
    if state.get('saved_picks'):
        state.setdefault('pick_history', [])
        state['pick_history'].append({
            'date': now.strftime('%Y-%m-%d'),
            'picks': state['saved_picks'],
        })
        # Keep only last 3 days
        three_days_ago = (now - datetime.timedelta(days=3)).strftime('%Y-%m-%d')
        state['pick_history'] = [
            d for d in state['pick_history'] if d.get('date', '') >= three_days_ago
        ]

    # Save today's picks for price monitoring (score >= 75)
    watch_list = [s for s in stocks if s.get('score', 0) >= 75]
    state['saved_picks'] = {
        s.get('ticker'): {
            'name': s.get('company_name', s.get('name', '')),
            'score': s.get('score'),
            'entry_price': s.get('price'),
            'pe_target': s.get('pe_target'),
            'saved_at': now.isoformat(),
        }
        for s in watch_list[:10]
    }
    save_state(state)

    # Post the tweet
    result = format_top5_tweet(stocks)
    if result:
        state['last_scan_tweet'] = now.isoformat()
        save_state(state)
    return bool(result)


# ===== MAIN CLI (for local testing / cron-job.org) =====
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AI Market Cap Twitter Engine")
    parser.add_argument("--post-scan", action="store_true", help="Post top 5 picks from latest scan")
    parser.add_argument("--check-alerts", action="store_true", help="Check price targets and post alerts")
    parser.add_argument("--all", action="store_true", help="Run both post-scan and alerts")
    args = parser.parse_args()

    if args.all or args.post_scan:
        print("[X] Posting daily scan...")
        post_daily_scan_to_twitter()

    if args.all or args.check_alerts:
        print("[X] Checking price alerts...")
        state = load_state()
        results = check_price_alerts(state)
        save_state(state)
        print(f"[X] Alerts checked. Posted: {results}")
