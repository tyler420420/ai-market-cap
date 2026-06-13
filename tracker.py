"""
AI Market Cap Tracker - Twitter Bot
Monitors aismarketcap.com picks and tweets when stocks hit PE targets
Run standalone, separate from web scanner
"""
import os, time, json, re
from datetime import datetime, timedelta
from threading import Thread

try:
    import tweepy
    TWEEPY_OK = True
except:
    TWEEPY_OK = False

try:
    import yfinance as yf
    YF_OK = True
except:
    YF_OK = False

import requests
from bs4 import BeautifulSoup

# ============ CONFIG ============
TWITTER_CREDS = {
    'api_key': os.environ.get('X_API_KEY', 'ptD4IFlECfhYAYiCIS2ueJcNb'),
    'api_secret': os.environ.get('X_API_SECRET', 'zZL8q7mClA75UPCtgiWLbrqrUaNXsOkVzTlhsQDD8ImnVskCsK'),
    'access_token': os.environ.get('X_ACCESS_TOKEN', '2034074541757222912-GrzIxt79lOdpbxSYsc1XUfpXpFwC4o'),
    'access_secret': os.environ.get('X_ACCESS_SECRET', 'qRXpfp30a5LU2nqvbYT4FZj73SQxjTJHgrt6CjzuTIt5m'),
}

SCANNER_URL = 'https://aismarketcap.com'
STATE_FILE = 'tracker_state.json'
LOG_FILE = 'tracker.log'
TWEET_COOLDOWN_HOURS = 3  # Minimum hours between tweets about same stock

# ============ LOGGING ============
def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

# ============ STATE MANAGEMENT ============
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {'picks': [], 'tweeted_targets': {}, 'last_scan': None}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

# ============ TWITTER ============
def get_twitter_api():
    if not TWEEPY_OK:
        log("[TWITTER] tweepy not installed")
        return None
    try:
        client = tweepy.Client(
            consumer_key=TWITTER_CREDS['api_key'],
            consumer_secret=TWITTER_CREDS['api_secret'],
            access_token=TWITTER_CREDS['access_token'],
            access_token_secret=TWITTER_CREDS['access_secret'],
        )
        return client
    except Exception as e:
        log(f"[TWITTER] Auth failed: {e}")
        return None

def tweet(msg):
    api = get_twitter_api()
    if not api:
        log("[TWITTER] Not available")
        return False
    try:
        api.create_tweet(text=msg)
        log(f"[TWITTER] Posted: {msg[:80]}...")
        return True
    except Exception as e:
        log(f"[TWITTER] Post failed: {e}")
        return False

# ============ FETCH SCANNER ============
def fetch_scanner_picks():
    log("[SCANNER] Fetching aismarketcap.com...")
    try:
        resp = requests.get(SCANNER_URL, timeout=30)
        html = resp.text
        soup = BeautifulSoup(html, 'html.parser')
        
        picks = []
        
        # Parse stock table from rowsData
        script_tags = soup.find_all('script')
        for script in script_tags:
            if script.string and 'rowsData' in script.string:
                # Extract JSON
                match = re.search(r'rowsData\s*=\s*(\[.*?\]);', script.string, re.DOTALL)
                if match:
                    data = json.loads(match.group(1))
                    for stock in data:
                        if stock.get('score', 0) >= 86:  # Strong Buy threshold
                            picks.append({
                                'ticker': stock['ticker'],
                                'name': stock['company_name'],
                                'score': stock['score'],
                                'price': stock['price'],
                                'pe_target': stock['pe_target'],
                                'pe_upside': stock.get('pe_upside', 0),
                                'earnings': stock.get('earnings_date', '').replace('<br>', ' '),
                            })
                    break
        
        # Also grab AI Suggested Trade from banner
        banner = soup.find('div', class_='pick-banner') or soup.find('div', style=lambda x: x and 'AI' in str(x) if x else False)
        ai_pick = None
        if banner:
            text = banner.get_text()
            ticker_match = re.search(r'([A-Z]{1,5})\s', text)
            score_match = re.search(r'Score[:\s]*(\d+)', text)
            target_match = re.search(r'Sell[:\s]*\$?([\d.]+)', text)
            if ticker_match and score_match:
                ai_pick = {
                    'ticker': ticker_match.group(1),
                    'score': int(score_match.group(1)),
                    'target': float(target_match.group(1)) if target_match else None,
                }
        
        log(f"[SCANNER] Found {len(picks)} Strong Buy picks + AI pick: {ai_pick}")
        return picks, ai_pick
        
    except Exception as e:
        log(f"[SCANNER] Fetch error: {e}")
        return [], None

# ============ PRICE MONITORING ============
def get_current_price(ticker):
    if not YF_OK:
        return None
    try:
        stock = yf.Ticker(ticker)
        info = stock.fast_info
        return info.get('last_price') or info.get('previous_close')
    except:
        return None

def check_targets(state):
    """Check if any picks from the last 3 days have hit their PE targets."""
    if os.environ.get("DISABLE_ALERTS") == "1":
        return []
    now = datetime.now()
            # Target: 6:35 AM PT (UTC-7 = 13:35 UTC-ish, but handle PDT/PST)
            target_hour = 6
            target_min = 35
            
            current_hour = now.hour
            current_min = now.minute
            
            # Simple: if between 6:30-6:40 AM, run
            if current_hour == target_hour and 30 <= current_min <= 40:
                log(f"[SCHEDULE] Running daily scan at {now}")
                run_daily_scan()
                time.sleep(600)  # Sleep 10 min to avoid re-run
            else:
                # Check targets every 2 hours
                if current_min == 0 and current_hour % 2 == 0:
                    state = load_state()
                    tweets = check_targets(state)
                    for t in tweets:
                        msg = format_target_tweet(t)
                        tweet(msg)
                        save_state(state)
                    time.sleep(120)
            
            time.sleep(30)
    else:
        # Continuous monitoring
        while True:
            state = load_state()
            tweets = check_targets(state)
            for t in tweets:
                msg = format_target_tweet(t)
                tweet(msg)
                save_state(state)
            time.sleep(7200)  # Check every 2 hours

if __name__ == '__main__':
    import sys
    max_retries = 10
    retry_count = 0
    while True:
        try:
            main()
        except Exception as e:
            retry_count += 1
            if retry_count > max_retries:
                log(f"[FATAL] Max retries ({max_retries}) exceeded, exiting")
                sys.exit(1)
            wait = min(300, 60 * retry_count)  # 1min, 2min, ... up to 5min
            log(f"[ERROR] Tracker crashed: {e}, restarting in {wait}s (attempt {retry_count}/{max_retries})")
            time.sleep(wait)