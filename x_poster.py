"""
X/Twitter Posting Engine for AI Market Cap Scanner
Posts top picks, monitors mentions, auto-replies, daily scan summaries.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os, json, sys as _sys, time, re, datetime
from pathlib import Path
from datetime import datetime as dt, time as dtime, timezone, timedelta
import tweepy
import requests

# ===== CREDENTIALS =====
X_API_KEY = os.environ.get("X_API_KEY", "yOvLpBE3bmoaHF4v4olSBvzSq")
X_API_SECRET = os.environ.get("X_API_KEY_SECRET", "GK4km93HgItjtcNWMYx6aZJm0NQqCMvQkQSMF8dpAusMkP5TtI")
X_ACCESS_TOKEN = os.environ.get("X_ACCESS_TOKEN", "2034074541757222912-GJFLycW2v5iMAlQnTdFyTJT46Q88rA")
X_ACCESS_SECRET = os.environ.get("X_ACCESS_TOKEN_SECRET", "PpA26ZjLMp14udxIWf8HUX1mTqUMsFBYFbKUFDaGn1hsf")

PT = timezone(timedelta(hours=-7))
CLIENT = None

def get_client():
    global CLIENT
    if CLIENT is None:
        CLIENT = tweepy.Client(
            consumer_key=X_API_KEY,
            consumer_secret=X_API_SECRET,
            access_token=X_ACCESS_TOKEN,
            access_token_secret=X_ACCESS_SECRET,
            wait_on_rate_limit=True
        )
    return CLIENT

def post_tweet(text):
    """Post a tweet. Returns tweet ID."""
    client = get_client()
    resp = client.create_tweet(text=text)
    tweet_id = resp.data['id']
    print(f"[X] Posted tweet {tweet_id}: {text[:80]}...")
    return tweet_id

def post_reply(tweet_id, text):
    """Reply to a tweet."""
    client = get_client()
    resp = client.create_tweet(text=text, in_reply_to_tweet_id=tweet_id)
    print(f"[X] Replied to {tweet_id}: {text[:80]}...")
    return resp.data['id']

def get_mentions(since_id=None):
    """Get recent mentions of @AIMoneyMach."""
    client = get_client()
    tweets = client.get_users_tweets(
        id="Aimoneymachine",  # This is wrong - we need the user ID, fix below
        expansions=["author_id"],
        max_results=20
    )
    return tweets

def get_mentions_by_search(since_id=None):
    """Search for recent mentions via mentions endpoint."""
    client = get_client()
    # Get user ID for @AIMoneyMach
    user = client.get_user(username="Aimoneymachine")
    user_id = user.data.id

    # Get mentions timeline
    tweets = client.get_users_mentions(
        id=user_id,
        expansions=["author_id"],
        max_results=20,
        tweet_fields=["created_at", "conversation_id"]
    )
    return tweets

def get_my_tweets(since_id=None):
    """Get recent tweets by @AIMoneyMach."""
    client = get_client()
    user = client.get_user(username="Aimoneymachine")
    user_id = user.data.id
    tweets = client.get_users_tweets(
        id=user_id,
        max_results=10,
        tweet_fields=["created_at"]
    )
    return tweets

def delete_tweet(tweet_id):
    """Delete a tweet by ID."""
    client = get_client()
    client.delete_tweet(tweet_id)
    print(f"[X] Deleted tweet {tweet_id}")


# ===== CONTENT GENERATORS =====

def generate_pick_tweet(stock, site_url="https://aismarketcap.com"):
    """Generate tweet for top pick."""
    ticker = stock['ticker']
    score = stock['score']
    price = stock.get('price', 0)
    pe_target = stock.get('pe_target', 0)
    days_left = stock.get('days_left', 0)
    sentiment = stock.get('sentiment', '')

    if score >= 86:
        label = "🔥 STRONG BUY"
    elif score >= 80:
        label = "📈 BUY"
    else:
        label = "👀 WATCH"

    tweet = f"{label} ${ticker} | Score {score}\n"
    tweet += f"Price: ${price} | PE Target: ${pe_target}\n"
    tweet += f"Earnings in {days_left} days"
    if sentiment and sentiment != '—':
        tweet += f" | {sentiment} earnings trend"
    tweet += f"\n\n📊 Full scan: {site_url}"
    tweet += f"\n\n#AIStocks #EarningsSeason"

    return tweet

def generate_scan_summary_tweet(num_stocks, top_tickers, site_url="https://aismarketcap.com"):
    """Daily scan summary tweet."""
    top_str = " $".join(top_tickers[:3])
    if top_str:
        top_str = " $" + top_str

    tweet = f"📊 Daily AI Earnings Scan: {num_stocks} stocks in range\n"
    tweet += f"Top picks:{top_str}\n"
    tweet += f"Full scanner: {site_url}"
    tweet += f"\n\n#AIStocks #PreEarnings"

    return tweet

def generate_market_comment_tweet():
    """Quick market commentary tweet."""
    tweets = [
        "Pre-earnings momentum is one of the most reliable short-term edges. Options implied volatility tells you exactly what the market expects. The question is whether the stock beats it. 🤖📊",
        "AI sector earnings are coming fast. Stocks with high analyst conviction + strong buy ratings tend to surprise to the upside more often. Data doesn't lie. 🚀",
        "Options flow before earnings is the market's real-time vote. Straddle prices encode the collective expectation. Our scanner surfaces the best setups. 🔍",
        "Score 80+ means institutional backing + bullish analyst consensus + high implied move potential. That's the pre-earnings edge. 💰",
    ]
    import random
    return random.choice(tweets)


# ===== SCANNER INTEGRATION =====

def get_latest_scan():
    """Load latest scan data from scanner HTML."""
    workspace = Path(__file__).parent
    scan_file = workspace / "ai_earnings_today.html"
    if not scan_file.exists():
        print("[X] No scan file found")
        return None

    content = scan_file.read_text(encoding='utf-8')
    idx = content.find('var rowsData=')
    if idx < 0:
        print("[X] No rowsData found")
        return None

    arr_depth, json_end = 0, idx
    for i in range(idx + 12, len(content)):
        ch = content[i]
        if ch == '[': arr_depth += 1
        elif ch == ']':
            arr_depth -= 1
            if arr_depth == 0:
                json_end = i
                break

    json_str = content[idx + 13:json_end + 1]  # +13 to skip 'var rowsData=' (17 chars total - 4 for 'var ')
    try:
        import json as json_lib
        data = json_lib.loads(json_str)
        return data
    except Exception as e:
        # Clean up HTML artifacts in JSON (e.g. <br> tags from earnings_date)
        clean = re.sub(r'<br\s*/?>', ' ', json_str)
        clean = re.sub(r"chr\(\d+\)", " ", clean)
        try:
            return json_lib.loads(clean)
        except Exception as e2:
            print(f"[X] JSON parse error: {e2}, clean error: {e2}")
            return None


# ===== MENTION MONITORING =====

TRACKED_TERMS = [
    "AI Market Cap", "aismarketcap", "AI earnings scanner",
    "pre-earnings", "AI stock momentum", "@Aimoneymachine",
    "stock before earnings", "AI stock scanner"
]

SEEN_MENTIONS_FILE = Path(__file__).parent / "seen_mentions.json"

def load_seen_mentions():
    if SEEN_MENTIONS_FILE.exists():
        return set(json.loads(SEEN_MENTIONS_FILE.read_text()))
    return set()

def save_seen_mentions(seen):
    SEEN_MENTIONS_FILE.write_text(json.dumps(list(seen)))

def get_user_id(username):
    """Get user ID for a username."""
    client = get_client()
    resp = client.get_user(username=username)
    return resp.data.id

def monitor_and_reply():
    """Check for new mentions and reply to relevant ones."""
    try:
        client = get_client()
        user_id = get_user_id("Aimoneymachine")
    except Exception as e:
        print(f"[X] Auth error (may need to re-check app permissions): {e}")
        return

    seen = load_seen_mentions()

    try:
        mentions = client.get_users_mentions(
            id=user_id,
            max_results=20,
            expansions=["author_id"],
            tweet_fields=["author_id", "created_at", "conversation_id"]
        )
    except Exception as e:
        print(f"[X] Error fetching mentions: {e}")
        return

    if not mentions.data:
        return

    # Get author info
    users = {u.id: u.username for u in mentions.includes.get("users", [])}

    for tweet in mentions.data:
        tweet_id = str(tweet.id)
        if tweet_id in seen:
            continue

        author = users.get(tweet.author_id, "unknown")
        text = tweet.text.lower()

        # Reply logic
        reply = None

        if any(term in text for term in ["how does it work", "how do i use", "what is this"]):
            reply = f"@{author} It's an AI pre-earnings momentum scanner. We score AI stocks on analyst conviction, buy%, and implied move potential. Score 80+ = strong buy signal. Free daily scan at https://aismarketcap.com"
        elif any(term in text for term in ["pricing", "cost", "how much", "subscribe"]):
            reply = f"@{author} $149/month or $999/year. Subscribers get 2 extra scans/day + AI chat. Free scan runs daily at 6:30 AM PT at https://aismarketcap.com/pricing"
        elif any(term in text for term in ["score", "scoring", "methodology"]):
            reply = f"@{author} Score = Analyst coverage (30pts) + Buy% (30pts) + 5D upside (20pts) + Strong Buy count (20pts max). 80+ = strong buy. Full explainer: https://aismarketcap.com/about"
        elif any(term in text for term in ["buy", "watch", "pick", "recommend"]):
            stocks = get_latest_scan()
            if stocks and len(stocks) > 0:
                top = stocks[0]
                reply = f"@{author} Today's top pick: ${top['ticker']} (Score {top['score']}). Earnings in {top['days_left']} days. PE target ${top['pe_target']}. Full scan: https://aismarketcap.com"
            else:
                reply = f"@{author} Check the daily scan for top picks: https://aismarketcap.com"
        elif any(term in text for term in ["free", "trial", "try"]):
            reply = f"@{author} Free scan runs daily at 6:30 AM PT automatically! No signup needed. Subscribe for extra scans + AI chat: https://aismarketcap.com/pricing"

        if reply:
            try:
                post_reply(tweet_id, reply)
                seen.add(tweet_id)
            except Exception as e:
                print(f"[X] Reply error: {e}")

    save_seen_mentions(seen)


# ===== SCHEDULED POSTING =====

def post_daily_scan():
    """Post top picks from latest scan."""
    stocks = get_latest_scan()
    if not stocks or len(stocks) == 0:
        print("[X] No stocks found in scan")
        return

    # Post top 3 picks
    for stock in stocks[:3]:
        try:
            tweet = generate_pick_tweet(stock)
            if len(tweet) > 280:
                tweet = tweet[:277] + "..."
            post_tweet(tweet)
            time.sleep(5)  # Space out posts
        except Exception as e:
            print(f"[X] Post error: {e}")

    # Post summary
    top_tickers = [s['ticker'] for s in stocks[:3]]
    summary = generate_scan_summary_tweet(len(stocks), top_tickers)
    try:
        post_tweet(summary)
    except Exception as e:
        print(f"[X] Summary post error: {e}")


def post_market_comment():
    """Post market commentary."""
    tweet = generate_market_comment_tweet()
    try:
        post_tweet(tweet)
    except Exception as e:
        print(f"[X] Comment post error: {e}")


# ===== MAIN =====
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="X/Twitter posting engine for AI Market Cap")
    parser.add_argument("--post-scan", action="store_true", help="Post daily scan picks")
    parser.add_argument("--post-comment", action="store_true", help="Post market commentary")
    parser.add_argument("--monitor", action="store_true", help="Monitor and reply to mentions")
    parser.add_argument("--all", action="store_true", help="Run everything")
    args = parser.parse_args()

    if args.all or args.post_scan:
        print("[X] Posting daily scan...")
        post_daily_scan()

    if args.all or args.post_comment:
        print("[X] Posting market comment...")
        post_market_comment()

    if args.all or args.monitor:
        print("[X] Monitoring mentions...")
        monitor_and_reply()

    if not any([args.post_scan, args.post_comment, args.monitor, args.all]):
        # Default: run everything
        print("[X] Running full X engine...")
        post_market_comment()
        time.sleep(3)
        post_daily_scan()
        time.sleep(5)
        monitor_and_reply()