"""
X/Twitter Posting Engine for AI Market Cap Scanner
Posts top picks + fires winning trade alerts when PE targets are hit.
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
    """Get OAuth1 auth object for Twitter v2 API."""
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
            data=payload,
            auth=get_twitter_auth(),
            headers={'Content-Type': 'application/json'},
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
    return {'tweeted_picks': {}, 'tweeted_targets': {}}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state))


# ===== TWEET CONTENT GENERATORS =====
def format_top6_tweet(stocks):
    """Post top 6 Strong Buy picks after daily scan.
    Twitter allows only 1 cashtag per tweet — top pick gets $, rest are plain text.
    """
    strong = [s for s in stocks if s.get('score', 0) >= 86]
    if not strong:
        print("[X] No Strong Buy picks to post")
        return False

    top6 = strong[:6]
    top = top6[0]
    rest = top6[1:]

    ticker = top.get('ticker', '?')
    score = top.get('score', 0)
    price = top.get('price', 0)
    pe_target = top.get('pe_target', 0)
    pe_upside = top.get('pe_upside', 0)
    days = top.get('days_left', top.get('days_to_earnings', '?'))

    # Build rest-of-list (no $ to avoid cashtag limit)
    rest_str = ' / '.join(s.get('ticker', '?') for s in rest[:5]) if rest else ''

    now = datetime.datetime.now(PT)
    day_str = now.strftime('%b %d')  # "May 28"

    lines = [
        f"🔥 ${ticker} | Score {score} | {day_str}",
        f"${price:.0f} → ${pe_target:.0f} (+{pe_upside:.0f}%) | Earnings in {days}d",
    ]
    if rest_str:
        lines.append(f"Also watching: {rest_str}")

    lines.append(f"📊 {SITE_URL}")
    lines.append("#AIStocks #PreEarnings")

    msg = '\n'.join(lines)
    if len(msg) > 280:
        msg = msg[:277] + "..."

    return post_tweet(msg)


def format_target_hit_tweet(ticker, name, current, target, pe_upside, gain_pct):
    """Tweet when a PE target is hit."""
    lines = [
        f"🎯 TARGET HIT! ${ticker} ({name})",
        f"Price: ${current:.0f} | Target: ${target:.0f}",
        f"Gain: +{gain_pct:.0f}% | PE Upside Called: +{pe_upside:.0f}%",
        "",
        f"Track top AI picks: {SITE_URL}",
        "#AIStocks #WinningTrade #OptionsTrading"
    ]
    msg = '\n'.join(lines)
    if len(msg) > 280:
        msg = msg[:277] + "..."
    return post_tweet(msg)


def format_milestone_tweet(ticker, name, current, target, gain_pct):
    """Tweet when a stock hits 5%+ without hitting PE target yet."""
    lines = [
        f"💰 ${ticker} ({name}) at +{gain_pct:.0f}%",
        f"Current: ${current:.0f} | PE Target: ${target:.0f}",
        f"",
        f"📊 Full scan: {SITE_URL}",
        "#AIStocks #PreEarnings"
    ]
    msg = '\n'.join(lines)
    if len(msg) > 280:
        msg = msg[:277] + "..."
    return post_tweet(msg)


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
    """Check if any saved picks have hit PE targets or 5%+ milestones."""
    picks = state.get('saved_picks', [])
    if not picks:
        print("[X] No saved picks to check")
        return []

    tweets = []
    now = datetime.datetime.now(PT)

    for pick in picks:
        ticker = pick['ticker']
        pe_target = pick['pe_target']
        buy_price = pick['entry_price']

        # Check cooldown
        last_tweet = state.get('tweeted_targets', {}).get(ticker)
        if last_tweet:
            last = datetime.datetime.fromisoformat(last_tweet)
            hours_since = (now - last).total_seconds() / 3600
            if hours_since < TWEET_COOLDOWN_HOURS:
                continue

        current = get_current_price(ticker)
        if not current:
            continue

        gain_pct = ((current - buy_price) / buy_price) * 100 if buy_price > 0 else 0

        print(f"[X] {ticker}: ${current:.2f} | Target: ${pe_target:.2f} | Gain: {gain_pct:.1f}%")

        if current >= pe_target:
            # PE target hit — winning trade!
            tweet_id = format_target_hit_tweet(
                ticker, pick.get('name', ''), current, pe_target,
                pick.get('pe_upside', 0), gain_pct
            )
            if tweet_id:
                state['tweeted_targets'][ticker] = now.isoformat()
                tweets.append(('target_hit', ticker))
                print(f"[X] TARGET HIT! ${ticker} posted")

        elif gain_pct >= 5:
            # 5% milestone — partial win tweet
            tweet_id = format_milestone_tweet(ticker, pick.get('name', ''), current, pe_target, gain_pct)
            if tweet_id:
                state['tweeted_targets'][ticker] = now.isoformat()
                tweets.append(('milestone', ticker))
                print(f"[X] MILESTONE! ${ticker} at +{gain_pct:.0f}% posted")

    return tweets


# ===== POST SCAN (called by scanner_web.py /cron endpoint) =====
def post_daily_scan_to_twitter():
    """Post top 6 picks after a scan run. Called from scanner_web.py."""
    print("[X] Posting daily scan to Twitter...")
    state = load_state()
    stocks = load_latest_scan()

    if not stocks:
        print("[X] No stocks found in scan")
        return False

    # Filter to strong buys
    strong = [s for s in stocks if s.get('score', 0) >= 86]
    if not strong:
        print("[X] No Strong Buy picks in scan")
        return False

    # Save picks for price monitoring
    state['saved_picks'] = [
        {
            'ticker': s.get('ticker'),
            'name': s.get('company_name', s.get('name', '')),
            'score': s.get('score'),
            'entry_price': s.get('price'),
            'pe_target': s.get('pe_target'),
            'pe_upside': s.get('pe_upside', 0),
            'saved_at': datetime.datetime.now(PT).isoformat(),
        }
        for s in strong[:6]
    ]
    save_state(state)

    # Post the tweet
    result = format_top6_tweet(stocks)
    if result:
        state['last_scan_tweet'] = datetime.datetime.now(PT).isoformat()
        save_state(state)
    return bool(result)


# ===== MAIN CLI (for local testing / cron-job.org) =====
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AI Market Cap Twitter Engine")
    parser.add_argument("--post-scan", action="store_true", help="Post top 6 picks from latest scan")
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
