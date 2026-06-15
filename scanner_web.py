"""AI Earnings Scanner -- Web + Background Scanner Server (Railway Deploy)"""
import os, hashlib, secrets, time, subprocess, threading, sys, json, re
from pathlib import Path
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo
from flask import Flask, request, redirect, send_from_directory, abort, make_response, jsonify

# ===== STRIPE CONFIG =====
import stripe
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

# Price IDs from Stripe dashboard
PRICE_MONTHLY = "price_1TZJ6JQtzL43j3LFo67RAb0m"
PRICE_ANNUAL = "price_1TZJ6iQtzL43j3LFZseI7iuP"

# ===== APP CONFIG =====
PORT = int(os.environ.get("PORT", 18766))
PT = ZoneInfo("America/Los_Angeles")
AUTO_SCAN_HOUR = 6
AUTO_SCAN_MINUTE = 30
COOKIE_NAME = "scanner_session"
SESSION_TTL = 86400

app = Flask(__name__, static_folder='static', static_url_path='/static')

# ===== HOME / SCANNER =====
@app.route("/")
def index():
    """Home page = scanner (no login required)"""
    workspace = Path(__file__).parent
    # Try fresh scan file first, then fall back to latest dated scan
    fresh = workspace / "ai_earnings_today.html"
    if fresh.exists():
        with open(fresh, 'r', encoding='utf-8') as f:
            content = f.read()
        resp = make_response(content)
        resp.headers['Content-Type'] = 'text/html; charset=utf-8'
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        return resp
    # Fall back to latest dated scan
    html_files = sorted(workspace.glob("ai_earnings_57day_*.html"), key=lambda f: f.stat().st_mtime, reverse=True)
    if html_files:
        with open(html_files[0], 'r', encoding='utf-8') as f:
            content = f.read()
        resp = make_response(content)
        resp.headers['Content-Type'] = 'text/html; charset=utf-8'
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        return resp
    # No scan yet - serve placeholder
    resp = make_response("""
    <!DOCTYPE html><html><head><meta charset="UTF-8"><title>AI Market Cap</title>
    <style>
        body { font-family: Segoe UI, sans-serif; background: #0d1117; color: #fff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; text-align: center; }
        h1 { color: #58a6ff; font-size: 2em; }
        p { color: #8b949e; }
        .btn { background: #238636; color: #fff; padding: 12px 24px; border: none; border-radius: 8px; font-size: 1em; cursor: pointer; text-decoration: none; display: inline-block; margin-top: 20px; }
    </style></head><body>
    <h1>AI Market Cap Scanner</h1>
    <p>No scan data yet. Run the scanner locally to generate reports.</p>
    <a href="/run" class="btn">Run Scanner</a>
    </body></html>""")
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    return resp

# ===== FAVICON =====
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.dirname(__file__), 'favicon.ico', mimetype='image/x-icon')

# ===== SCAN STATE =====
class ScanState:
    scan_state = 'idle'
    refresh_state = 'idle'

scan_state = ScanState()
_last_auto_scan_date = None

# ===== SUBSCRIPTION MANAGEMENT =====
# Simple file-based subscription store (for demo - use DB in production)
SUBS_FILE = Path(__file__).parent / "subscriptions.json"
SCAN_COUNTS_FILE = Path(__file__).parent / "scan_counts.json"
MAX_SCANS_PER_DAY = 2

def get_subscriptions():
    if SUBS_FILE.exists():
        try:
            return json.loads(SUBS_FILE.read_text())
        except:
            return {}
    return {}

def get_scan_counts():
    if SCAN_COUNTS_FILE.exists():
        try:
            return json.loads(SCAN_COUNTS_FILE.read_text())
        except:
            return {}
    return {}

def get_scans_today(customer_id):
    counts = get_scan_counts()
    today = datetime.now(PT).strftime("%Y-%m-%d")
    key = f"{customer_id}:{today}"
    return counts.get(key, 0)

def increment_scan_count(customer_id):
    counts = get_scan_counts()
    today = datetime.now(PT).strftime("%Y-%m-%d")
    key = f"{customer_id}:{today}"
    counts[key] = counts.get(key, 0) + 1
    save_scan_counts(counts)

def save_scan_counts(counts):
    # clean up old dates
    today = datetime.now(PT).strftime("%Y-%m-%d")
    counts = {k: v for k, v in counts.items() if k.split(":")[0] == today}
    SCAN_COUNTS_FILE.write_text(json.dumps(counts))

def save_subscription(customer_id, plan, status):
    subs = get_subscriptions()
    subs[customer_id] = {'plan': plan, 'status': status, 'updated': int(time.time())}
    SUBS_FILE.write_text(json.dumps(subs))

def check_subscription_by_session(session_token):
    """Check if session token has active subscription."""
    subs = get_subscriptions()
    return subs.get(session_token, {}).get('status') == 'active'

# ===== SESSION MANAGEMENT =====
def make_session():
    token = secrets.token_hex(32)
    expires = int(time.time()) + SESSION_TTL
    return f"{token}|{expires}"

def validate_session(token):
    if not token: return False
    try:
        token_str, exp_str = token.split("|")
        return time.time() < int(exp_str)
    except: return False

def set_session(resp, plan=None):
    token = make_session()
    resp.set_cookie(COOKIE_NAME, token, max_age=SESSION_TTL, httponly=True, samesite='Lax')
    if plan:
        subs = get_subscriptions()
        subs[token] = {'plan': plan, 'status': 'active', 'updated': int(time.time())}
        SUBS_FILE.write_text(json.dumps(subs))

# ===== SCANNER CORE =====
SCANNER_PATH = Path(__file__).parent / "ai_earnings_scanner.py"

def trigger_scan():
    scan_state.scan_state = 'running'
    scan_state.refresh_state = 'idle'
    print('[Scanner] Scan triggered.')
    t = threading.Thread(target=run_full_scan, daemon=True)
    t.start()

def run_full_scan():
    today_path = Path(__file__).parent / "ai_earnings_today.html"
    golden_path = Path(__file__).parent / "ai_earnings_golden.html"
    try:
        result = subprocess.run(
            [sys.executable, str(SCANNER_PATH)],
            capture_output=True, text=True,
            encoding='utf-8', errors='replace', timeout=180,
            cwd=str(Path(__file__).parent)
        )
        print('[Scanner] Full scan complete. Exit code:', result.returncode)
        # Validate output before going live - golden backup always wins if bad
        if today_path.exists():
            content = today_path.read_text(encoding='utf-8')
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
                stock_count = content.count('"ticker":')
                print(f'[Scanner] rowsData={json_len} bytes, stocks={stock_count}')
                if json_len >= 5000 and stock_count >= 3:
                    import shutil
                    shutil.copy2(today_path, golden_path)
                    print(f'[Scanner] VALID - golden updated ({stock_count} stocks)')
                else:
                    print(f'[Scanner] INVALID - restoring golden')
                    if golden_path.exists():
                        shutil.copy2(golden_path, today_path)
                        print('[Scanner] Restored from golden backup')
            else:
                print('[Scanner] No rowsData - restoring golden')
                if golden_path.exists():
                    shutil.copy2(golden_path, today_path)
        scan_state.scan_state = 'done'
    except Exception as e:
        print('[Scanner] Scan error:', e)
        if golden_path.exists():
            import shutil
            shutil.copy2(golden_path, today_path)
            print('[Scanner] Restored from golden after error')
        scan_state.scan_state = 'done'

def auto_scan_loop():
    global _last_auto_scan_date
    while True:
        now_pt = datetime.now(PT)
        today_date = now_pt.date()
        target = datetime.combine(today_date, dtime(AUTO_SCAN_HOUR, AUTO_SCAN_MINUTE), tzinfo=PT)
        if now_pt >= target:
            try:
                target = datetime.combine(today_date.replace(day=today_date.day + 1), dtime(AUTO_SCAN_HOUR, AUTO_SCAN_MINUTE), tzinfo=PT)
            except ValueError:
                target = datetime.combine(today_date.replace(month=today_date.month + 1, day=1), dtime(AUTO_SCAN_HOUR, AUTO_SCAN_MINUTE), tzinfo=PT)
        wait_seconds = (target - now_pt).total_seconds()
        print(f'[Auto-Scan] Next scan at {target.strftime("%Y-%m-%d %I:%M %p PT")} (in {wait_seconds/3600:.1f} hrs)')
        try:
            time.sleep(wait_seconds)
        except KeyboardInterrupt:
            break
        try:
            global _last_auto_scan_date
            if datetime.now(PT).date() != _last_auto_scan_date:
                trigger_scan()
                _last_auto_scan_date = datetime.now(PT).date()
        except Exception as e:
            print('[Auto-Scan] Error during scheduled scan:', e)

# ===== AUTO SCAN CRON =====

@app.route("/cron")
def cron():
    """Triggered by Railway cron job at 6:30 AM PT daily"""
    now = datetime.now(PT)
    today = now.date()
    force = request.args.get('force') == '1'
    if not force and getattr(cron, 'last_run', None) == today:
        return "Already ran today", 200
    cron.last_run = today

    def do_scan(label=""):
        today_path = Path(__file__).parent / "ai_earnings_today.html"
        golden_path = Path(__file__).parent / "ai_earnings_golden.html"

        # STEP 1: Run scan, capture result
        scan_succeeded = False
        try:
            result = subprocess.run(
                [sys.executable, str(Path(__file__).parent / "ai_earnings_scanner.py")],
                capture_output=True, text=True,
                encoding='utf-8', errors='replace', timeout=180,
                cwd=str(Path(__file__).parent)
            )
            # STEP 2: Validate - must have rowsData >= 5000 bytes AND at least 5 stocks
            if today_path.exists():
                content = today_path.read_text(encoding='utf-8')
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
                    stock_count = content.count('"ticker":')
                    print(f"[Cron{label}] rowsData={json_len} bytes, stocks={stock_count}")
                    if json_len >= 5000 and stock_count >= 5:
                        import shutil
                        shutil.copy2(today_path, golden_path)
                        print(f"[Cron{label}] VALID - Golden backup updated ({stock_count} stocks)")
                        scan_succeeded = True
                    else:
                        print(f"[Cron{label}] INVALID - rowsData={json_len} or stocks={stock_count} too low, restoring golden")
                        if golden_path.exists():
                            shutil.copy2(golden_path, today_path)
                        else:
                            print("[Cron] No golden backup found, leaving current file")
                else:
                    print(f"[Cron{label}] rowsData not found, restoring golden")
                    if golden_path.exists():
                        shutil.copy2(golden_path, today_path)
            print(f"[Cron{label}] Scan output:", result.stdout[-500:] if result.stdout else "no output")
        except Exception as e:
            print(f"[Cron{label}] Scan error: {e}")
            if golden_path.exists():
                import shutil
                shutil.copy2(golden_path, today_path)

        # STEP 3: Self-heal — if fewer than 12 stocks, re-run once automatically
        if scan_succeeded:
            heal_count = today_path.read_text(encoding='utf-8').count('"ticker":')
            if heal_count < 12:
                print(f"[Heal{label}] Only {heal_count} stocks, re-running scanner...")
                try:
                    result = subprocess.run(
                        [sys.executable, str(Path(__file__).parent / "ai_earnings_scanner.py")],
                        capture_output=True, text=True,
                        encoding='utf-8', errors='replace', timeout=180,
                        cwd=str(Path(__file__).parent)
                    )
                    new_content = today_path.read_text(encoding='utf-8')
                    new_count = new_content.count('"ticker":')
                    if new_count > heal_count:
                        import shutil
                        shutil.copy2(today_path, golden_path)
                        print(f"[Heal{label}] Re-scan improved to {new_count} stocks, golden updated")
                except Exception as e:
                    print(f"[Heal{label}] Re-scan error: {e}")

        # STEP 4: Done — Twitter post handled by /cron-twitter after morning scan only
        return scan_succeeded

    def do_afternoon():
        # Separate state tracking for afternoon scan
        now = datetime.now(PT)
        today = now.date()
        force = request.args.get('force') == '1'
        if not force and getattr(do_afternoon, 'last_run', None) == today:
            print("[Cron-Afternoon] Already ran today")
            return
        do_afternoon.last_run = today
        do_scan(label="[Afternoon]")

    threading.Thread(target=do_scan, daemon=True).start()
    return "Scan triggered", 200


@app.route("/cron-afternoon")
def cron_afternoon():
    """Triggered by cron-job.org at 1:00 PM PT daily"""
    def do_afternoon():
        now = datetime.now(PT)
        today = now.date()
        force = request.args.get('force') == '1'
        if not force and getattr(do_afternoon, 'last_run', None) == today:
            print("[Cron-Afternoon] Already ran today")
            return
        do_afternoon.last_run = today
        today_path = Path(__file__).parent / "ai_earnings_today.html"
        golden_path = Path(__file__).parent / "ai_earnings_golden.html"
        scan_succeeded = False
        try:
            result = subprocess.run(
                [sys.executable, str(Path(__file__).parent / "ai_earnings_scanner.py")],
                capture_output=True, text=True,
                encoding='utf-8', errors='replace', timeout=180,
                cwd=str(Path(__file__).parent)
            )
            if today_path.exists():
                content = today_path.read_text(encoding='utf-8')
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
                    stock_count = content.count('"ticker":')
                    print(f"[Cron-Afternoon] rowsData={json_len} bytes, stocks={stock_count}")
                    if json_len >= 5000 and stock_count >= 5:
                        import shutil
                        shutil.copy2(today_path, golden_path)
                        print(f"[Cron-Afternoon] VALID - Golden backup updated ({stock_count} stocks)")
                        scan_succeeded = True
                    else:
                        print(f"[Cron-Afternoon] INVALID, restoring golden")
                        if golden_path.exists():
                            shutil.copy2(golden_path, today_path)
                else:
                    if golden_path.exists():
                        shutil.copy2(golden_path, today_path)
            print("[Cron-Afternoon] Scan output:", result.stdout[-500:] if result.stdout else "no output")
        except Exception as e:
            print(f"[Cron-Afternoon] Scan error: {e}")
            if golden_path.exists():
                import shutil
                shutil.copy2(golden_path, today_path)
        if scan_succeeded:
            heal_count = today_path.read_text(encoding='utf-8').count('"ticker":')
            if heal_count < 12:
                print(f"[Heal-Afternoon] Only {heal_count} stocks, re-running...")
                try:
                    subprocess.run(
                        [sys.executable, str(Path(__file__).parent / "ai_earnings_scanner.py")],
                        capture_output=True, text=True,
                        encoding='utf-8', errors='replace', timeout=180,
                        cwd=str(Path(__file__).parent)
                    )
                    import shutil
                    shutil.copy2(today_path, golden_path)
                except Exception as e:
                    print(f"[Heal-Afternoon] Re-scan error: {e}")
    threading.Thread(target=do_afternoon, daemon=True).start()
    return "Afternoon scan triggered", 200


@app.route("/cron-twitter")
def cron_twitter():
    """Post top 6 picks to Twitter. Hit by cron-job.org after morning scan."""
    def do_twitter():
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from x_poster import post_daily_scan_to_twitter
            post_daily_scan_to_twitter()
        except Exception as e:
            print(f"[Cron-Twitter] Error: {e}")
    threading.Thread(target=do_twitter, daemon=True).start()
    return "Twitter post triggered", 200


@app.route("/cron-price-alerts")
def cron_price_alerts():
    """Disabled - alerts consume too many Twitter API credits."""
    return "Alerts disabled", 200

# ===== WEB ROUTES =====

@app.route("/robots.txt")
def robots():
    return "User-agent: *\nAllow: /\n\nSitemap: https://aismarketcap.com/sitemap.xml", 200, {"Content-Type": "text/plain"}

@app.route("/sitemap.xml")
def sitemap():
    today = datetime.now().strftime("%Y-%m-%d")
    # Dynamic: collect all wins_*.html files from the app directory
    app_dir = Path(__file__).parent
    static_pages = [
        ("/", 1.0),
        ("/wins", 0.8),
        ("/about", 0.8),
        ("/pricing", 0.9),
    ]
    wins_pages = []
    for f in app_dir.glob("wins_*.html"):
        ticker = f.stem.replace("wins_", "")
        wins_pages.append((f"/wins/{ticker}", 0.7))
    xml_urls = ""
    for loc, priority in static_pages:
        xml_urls += f"<url><loc>https://aismarketcap.com{loc}</loc><lastmod>{today}</lastmod><priority>{priority}</priority></url>"
    for loc, priority in wins_pages:
        xml_urls += f"<url><loc>https://aismarketcap.com{loc}</loc><lastmod>{today}</lastmod><priority>{priority}</priority></url>"
    xml = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{xml_urls}</urlset>'
    resp = make_response(xml)
    resp.headers["Content-Type"] = "application/xml"
    return resp
    html_files = sorted(workspace.glob("ai_earnings_57day_*.html"), key=lambda f: f.stat().st_mtime, reverse=True)
    if html_files:
        with open(html_files[0], 'r', encoding='utf-8') as f:
            content = f.read()
        content = content.replace('<script>setTimeout(function(){document.getElementById("sub-popup").classList.add("show")},300000)</script>',
                                  f'{sub_flag}<script>if(!window.isSubscribed){{setTimeout(function(){{document.getElementById("sub-popup").classList.add("show")}},300000)}}else{{document.getElementById("sub-popup")&&(document.getElementById("sub-popup").style.display="none")}}</script>')
        resp = make_response(content)
        resp.headers['Content-Type'] = 'text/html; charset=utf-8'
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        return resp
    resp = make_response("""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>AI Market Cap</title><style>body{font-family:Segoe UI,sans-serif;background:#0d1117;color:#fff;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;text-align:center}h1{color:#58a6ff;font-size:2em}p{color:#8b949e}.btn{background:#238636;color:#fff;padding:12px 24px;border:none;border-radius:8px;font-size:1em;cursor:pointer;text-decoration:none;display:inline-block;margin-top:20px}</style></head><body><h1>AI Market Cap Scanner</h1><p>Scanner is warming up. Check back in a few minutes.</p><a href="/pricing" class=btn>Subscribe to Unlock Full Access</a></body></html>""")
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    return resp

@app.route("/wins")
def wins():
    with open(Path(__file__).parent / "wins.html", 'r', encoding='utf-8') as f:
        content = f.read()
    resp = make_response(content)
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    return resp

@app.route("/calendar")
def calendar_page():
    with open(Path(__file__).parent / "calendar.html", 'r', encoding='utf-8') as f:
        content = f.read()
    resp = make_response(content)
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    return resp

# Dynamic wins ticker pages: /wins/<ticker> auto-serves wins_<ticker>.html
@app.route("/wins/<ticker>")
def wins_ticker_page(ticker):
    app_dir = Path(__file__).parent
    wins_file = app_dir / f"wins_{ticker}.html"
    if wins_file.exists():
        with open(wins_file, 'r', encoding='utf-8') as f:
            content = f.read()
        resp = make_response(content)
        resp.headers['Content-Type'] = 'text/html; charset=utf-8'
        return resp
    return "Wins page not found", 404

# Legacy hardcoded routes (keep for existing wins pages)
@app.route("/wins/okta")
def wins_okta():
    with open(Path(__file__).parent / "wins_okta.html", 'r', encoding='utf-8') as f:
        content = f.read()
    resp = make_response(content)
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    return resp

@app.route("/wins/snowflake")
def wins_snowflake():
    with open(Path(__file__).parent / "wins_snowflake.html", 'r', encoding='utf-8') as f:
        content = f.read()
    resp = make_response(content)
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    return resp

@app.route("/wins/innodata")
def wins_innodata():
    with open(Path(__file__).parent / "wins_innodata.html", 'r', encoding='utf-8') as f:
        content = f.read()
    resp = make_response(content)
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    return resp

@app.route("/pricing")
def pricing():
    """Pricing page with Stripe Checkout"""
    pricing_html = """<!DOCTYPE html>
<html><head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="icon" type="image/png" href="/static/logo.png">
    <meta name="description" content="Subscribe to run additional scans and use the AI Chat Analyst on the AI Market Cap Scanner.">
    <title>Pricing - AI Market Cap</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: Segoe UI, Arial, sans-serif; background: #0d1117; color: #c9d1d9; min-height: 100vh; }
.header { background: linear-gradient(135deg,#1a1f2e,#161b22); padding: 20px 30px; border-bottom: 1px solid #30363d; display: flex; justify-content: space-between; align-items: center; }
.header h1 { color: #58a6ff; font-size: 1.5em; }
.header a { color: #58a6ff; text-decoration: none; font-size: 0.9em; }
.container { max-width: 900px; margin: 0 auto; padding: 60px 20px; text-align: center; }
h2 { color: #fff; font-size: 2em; margin-bottom: 10px; }
.subtitle { color: #8b949e; font-size: 1.1em; margin-bottom: 50px; }
.plans { display: flex; gap: 20px; justify-content: center; flex-wrap: wrap; }
.plan { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 30px; width: 260px; text-align: left; }
.plan h3 { color: #fff; font-size: 1.2em; margin-bottom: 10px; }
.plan .price { font-size: 2.5em; font-weight: bold; color: #fff; margin-bottom: 5px; }
.plan .price span { font-size: 0.4em; color: #8b949e; font-weight: normal; }
.plan .period { color: #8b949e; font-size: 0.85em; margin-bottom: 25px; }
.plan ul { list-style: none; margin-bottom: 25px; }
.plan li { color: #c9d1d9; font-size: 0.88em; padding: 6px 0; }
.plan li::before { content: "✓ "; color: #2ea043; }
.plan li.off::before { content: "✗ "; color: #ff6b6b; }
.plan li.off { color: #6e7681; }
.plan .cta { display: block; background: #238636; color: #fff; text-align: center; padding: 12px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 0.95em; }
.plan .cta:hover { background: #2ea043; }
.plan.featured { border-color: #ffd700; box-shadow: 0 0 20px rgba(255,215,0,0.2); }
.plan.featured .cta { background: #238636; }
.plan.featured .cta:hover { background: #2ea043; }
.back-link { display: inline-block; margin-top: 40px; color: #58a6ff; text-decoration: none; font-size: 0.9em; }
.back-link:hover { color: #79b8ff; }
</style></head><body>
<div class=header>
    <h1><a href="/" style="color:#58a6ff;text-decoration:none">AI Market Cap</a></h1>
    <a href="/">View Scanner</a>
</div>

<div class=container>
    <h2>Subscribe for additional scans<br>and AI Chat Pro Trader.</h2>
    <p class=subtitle>Unlock full access to the scanner</p>
    <div class=plans>
        <div class=plan>
            <h3>Monthly</h3>
            <div class=price>$149<span>/mo</span></div>
            <div class=period>Billed monthly</div>
            <ul>
                <li>2 Additional Scans Per Day</li>
                <li>AI Chat Pro Trader</li>
            </ul>
            <a href="/create-checkout?plan=monthly" class=cta>Subscribe - $149/mo</a>
        </div>
        <div class=plan style="border-color:#ffd700;box-shadow:0 0 16px rgba(255,215,0,.3)">
            <h3>Annual</h3>
            <div class=price>$999<span>/yr</span></div>
            <div class=period>Save $789 vs monthly</div>
            <ul>
                <li>Everything in Monthly</li>
                <li>Save $789/year</li>
            </ul>
            <a href="/create-checkout?plan=annual" class=cta>Subscribe - $999/yr</a>
        </div>
    </div>
    <a href="/about" class=back-link>← Learn more about AI Market Cap</a>
</div>
</body></html>"""
    return make_response(pricing_html, 200, {"Content-Type": "text/html; charset=utf-8"})

@app.route("/about")
def about():
    about_html = """<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" type="image/png" href="/static/logo.png">
<title>How It Works - AI Market Cap</title>
<meta name="description" content="Learn how AI Market Cap's pre-earnings momentum scanner works. Scoring methodology, PE targets, 3-day and 5-day implied moves explained.">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: Segoe UI, Arial, sans-serif; background: #0d1117; color: #c9d1d9; min-height: 100vh; }
.header { background: linear-gradient(135deg,#1a1f2e,#161b22); padding: 20px 30px; border-bottom: 1px solid #30363d; display: flex; justify-content: space-between; align-items: center; }
.header h1 a { color: #58a6ff; font-size: 1.5em; text-decoration: none; }
.header a.nav-link { color: #58a6ff; text-decoration: none; font-size: 0.9em; }
.container { max-width: 800px; margin: 0 auto; padding: 40px 20px; }
h2 { color: #fff; font-size: 1.8em; margin: 35px 0 15px; border-bottom: 1px solid #30363d; padding-bottom: 10px; }
h2:first-child { margin-top: 0; }
h3 { color: #2ea043; font-size: 1.15em; margin: 20px 0 8px; }
p { color: #c9d1d9; font-size: 0.95em; line-height: 1.7; margin-bottom: 14px; }
ul { margin: 0 0 14px 20px; }
li { color: #c9d1d9; font-size: 0.95em; line-height: 1.7; margin-bottom: 6px; }
.faq-q { color: #ffd700; font-weight: bold; margin-bottom: 6px; }
.disclaimer { margin-top: 40px; padding: 16px 20px; background: #1a1a1a; border-radius: 8px; border: 1px solid #c0392b; color: #999; font-size: 0.8em; line-height: 1.6; }
.highlight { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; margin: 15px 0; }
.highlight strong { color: #2ea043; }
.toc { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px 25px; margin-bottom: 30px; }
.toc a { color: #58a6ff; text-decoration: none; display: block; padding: 4px 0; }
.toc a:hover { color: #79b8ff; }
</style></head><body>
<div class=header>
    <h1><a href="/">AI Market Cap</a></h1>
    <a href="/wins" class=nav-link>Wins</a>
    <a href="/pricing" class=nav-link>Subscribe</a>
</div>
<div class=container>
    <div class=toc>
        <a href="#methodology">Scoring Methodology</a>
        <a href="#targets">PE / 3D / 5D Targets</a>
        <a href="#ai">AI Suggested Trade</a>
        <a href="#faq">FAQ</a>
    </div>

    <h2 id=methodology>Scoring Methodology</h2>
    <p>Every stock is scored 0–100 based on five factors:</p>
    <div class=highlight>
        <strong>Analyst Coverage (25pts max)</strong> — Total analysts covering this stock, 1 point each up to 25. More coverage = higher score.<br><br>
        <strong>Buy % Conviction (25pts max)</strong> — Raw % of analysts with Buy or Strong Buy out of all ratings. We weight this to capture conviction level.<br><br>
        <strong>Strong Buy Count (20pts max)</strong> — Each Strong Buy rating adds 2 points. Stocks with 10+ Strong Buy ratings get the full 20 pts.<br><br>
        <strong>5D Upside (15pts max)</strong> — ATM straddle × 5, expressed as % of current stock price. Higher implied move potential = higher score.<br><br>
        <strong>Earnings Sentiment (15pts max)</strong> — Recent earnings history. Positive = 15pts, Mixed = 7pts, Negative = 0pts.
    </div>
    <p>Stocks scoring <strong style="color:#00ff88">75+</strong> are flagged Strong Buy. Stocks scoring <strong style="color:#58a6ff">50+</strong> are Watch.</p>

    <h2 id=targets>PE / 3-Day / 5-Day Target Columns</h2>
    <h3>PE Target</h3>
    <p>Estimated exit price using an ATM straddle at <strong>1× implied move</strong>. This is the conservative estimate — assumes the stock moves exactly what the options market expects, in the direction of the trend.</p>
    <h3>3-Day Target</h3>
    <p>Estimated exit price using an ATM straddle at <strong>3× implied move</strong>. Mid-range scenario for stocks 3–7 days from earnings.</p>
    <h3>5-Day Target</h3>
    <p>Estimated exit price using an ATM straddle at <strong>5× implied move</strong>. Maximum upside scenario — appropriate for stocks 5+ days out or high-IV names where the straddle is expensive.</p>
    <h3>What is a Straddle?</h3>
    <p>An ATM straddle buys both a call and a put at the same strike. Its value changes based on how much the stock moves, regardless of direction. We use the straddle price to back-calculate what stock move is being priced in by the market.</p>

    <h2 id=ai>AI Suggested Trade</h2>
    <p>The banner at the top highlights the best trade opportunity — the strong buy (score 75+) with the most days until earnings. Having more time to enter gives you flexibility and better positioning before the report.</p>
    <p>A runner-up pick is also shown — the 2nd best strong buy by days left. Both banners update automatically every scan.</p>
    <p>This is not financial advice. It's AI's trading observations on where the math and momentum align.</p>

    <h2 id=faq>Frequently Asked Questions</h2>
    <p class=faq-q>Is this a financial advisor service?</p>
    <p>No. AI Market Cap is a data tool for informational purposes only. We are not licensed financial advisors. Always do your own research.</p>
    <p class=faq-q>How often does the scanner update?</p>
    <p>The free scan runs automatically every market day at 6:30 AM PT. Subscribers can run up to 3 additional scans per day on demand.</p>
    <p class=faq-q>What data sources are used?</p>
    <p>Stock prices and option data come from Yahoo Finance. Analyst ratings are pulled from Yahoo Finance's recommendations endpoint. News is sourced from Yahoo Finance market articles.</p>
    <p class=faq-q>What does "days left" mean?</p>
    <p>Days until the next earnings report date. We show stocks within 40 days of reporting.</p>
    <p class=faq-q>What does Short % mean?</p>
    <p>Short interest - the percentage of shares that have been sold short and not yet covered. High short interest increases squeeze potential pre-earnings.</p>
    <p class=faq-q>What does IV mean?</p>
    <p>Implied Volatility — how much the options market expects the stock to move. High IV stocks have larger straddle targets and greater score potential.</p>
    <p class=faq-q>What does Earnings Trend mean?</p>
    <p>Positive = stock has beaten earnings estimates in recent quarters. Mixed = mixed results. Negative = missed recent estimates. This factor adds up to 15 points to the score.</p>
    <p class=faq-q>Can I trade based on this?</p>
    <p>You can, but AI Market Cap is not responsible for any gains or losses. This tool helps identify opportunities — the trade decision is always yours.</p>

    <div class=disclaimer>
        <strong>Disclaimer:</strong> AI Market Cap is for informational purposes only. Options data and price targets are estimates based on ATM straddles — actual results may vary. This is not a financial advisor service. Always do your own research before trading. AI Market Cap is not liable for any losses incurred from trades based on this data.
    </div>
</div>
</body></html>"""
    return make_response(about_html, 200, {"Content-Type": "text/html; charset=utf-8"})

@app.route("/create-checkout")
def create_checkout():
    """Create Stripe Checkout session"""
    plan = request.args.get('plan', 'monthly')
    price_id = PRICE_ANNUAL if plan == 'annual' else PRICE_MONTHLY
    plan_name = 'Annual' if plan == 'annual' else 'Monthly'

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.host_url + 'success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.host_url + 'pricing',
            allow_promotion_codes=True,
            metadata={'plan': plan}
        )
        return redirect(session.url, code=302)
    except Exception as e:
        return f"Error creating checkout: {e}", 500

@app.route("/success")
def success():
    """Payment success page"""
    session_id = request.args.get('session_id', '')
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        customer_id = session.customer
        plan = session.metadata.get('plan', 'monthly')

        # Grant access
        subs = get_subscriptions()
        subs[customer_id] = {'plan': plan, 'status': 'active', 'updated': int(time.time())}
        SUBS_FILE.write_text(json.dumps(subs))

        success_html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Welcome - AI Market Cap</title>
<style>
body {{ font-family: Segoe UI, sans-serif; background: #0d1117; color: #fff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; text-align: center; }}
h1 {{ color: #2ea043; font-size: 2em; }}
p {{ color: #8b949e; font-size: 1.1em; margin: 20px 0; }}
a {{ background: #238636; color: #fff; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold; }}
</style></head><body>
<h1>✓ Payment Successful!</h1>
<p>Welcome to AI Market Cap! Your {plan_name} subscription is now active.</p>
<p>Click below to access your scanner.</p>
<a href="/">Go to Scanner →</a>
</body></html>"""
        resp = make_response(success_html, 200, {"Content-Type": "text/html; charset=utf-8"})
        resp.set_cookie("stripe_customer", customer_id, max_age=86400*30, httponly=True, samesite='Lax')
        return resp
    except Exception as e:
        return f"Error: {e}", 500

@app.route("/api/scans", methods=["GET"])
def api_scans():
    customer_id = request.cookies.get("stripe_customer", "")
    token = request.cookies.get(COOKIE_NAME, "")
    used = get_scans_today(customer_id) if customer_id else get_scans_today(token)
    return jsonify({'used': used, 'limit': MAX_SCANS_PER_DAY, 'remaining': max(0, MAX_SCANS_PER_DAY - used)})

@app.route("/webhook", methods=["POST"])
def webhook():
    """Stripe webhook handler"""
    payload = request.data
    sig = request.headers.get('Stripe-Signature', '')

    if STRIPE_WEBHOOK_SECRET:
        try:
            event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
        except Exception as e:
            return f"Webhook error: {e}", 400
    else:
        event = json.loads(payload)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        customer_id = session.get('customer')
        plan = session.get('metadata', {}).get('plan', 'monthly')
        save_subscription(customer_id, plan, 'active')
        print(f"[Webhook] Subscription activated for customer: {customer_id}")

    elif event['type'] == 'customer.subscription.deleted':
        sub = event['data']['object']
        customer_id = sub.get('customer')
        subs = get_subscriptions()
        if customer_id in subs:
            subs[customer_id]['status'] = 'cancelled'
            SUBS_FILE.write_text(json.dumps(subs))
        print(f"[Webhook] Subscription cancelled for customer: {customer_id}")

    return "ok", 200

@app.route("/run", methods=["POST"])
def api_run():
    """"Run scan - requires active subscription + max 2/day"""
    token = request.cookies.get(COOKIE_NAME, "")
    customer_id = request.cookies.get("stripe_customer", "")

    # Check subscription
    subs = get_subscriptions()
    is_active = subs.get(customer_id, {}).get('status') == 'active' or subs.get(token, {}).get('status') == 'active'

    if not is_active:
        return redirect("/pricing")

    # Check scan limit
    key_id = customer_id if customer_id else token
    if get_scans_today(key_id) >= MAX_SCANS_PER_DAY:
        return jsonify({'error': 'limit_reached', 'message': f'Daily scan limit reached ({MAX_SCANS_PER_DAY}/day). Try again tomorrow.'}), 429

    trigger_scan()
    increment_scan_count(key_id)
    return "ok"

@app.route("/status")
def api_status():
    return jsonify({
        'scan_state': scan_state.scan_state,
        'refresh_state': scan_state.refresh_state
    })

@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Chat - requires active subscription"""
    customer_id = request.cookies.get("stripe_customer", "")
    subs = get_subscriptions()
    is_active = subs.get(customer_id, {}).get('status') == 'active'

    if not is_active:
        return redirect("/pricing")

    try:
        body = request.get_json(force=True)
    except Exception:
        body = {}
    user_msg = (body.get("message") or "").strip()
    if not user_msg:
        return jsonify({"error": "No message provided"}), 400
    if len(user_msg) > 1000:
        return jsonify({"error": "Message too long (max 1000 chars)"}), 400

    reply = call_llm(user_msg)
    return jsonify({"reply": reply})


# ===== LLM (GROQ) =====
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

def call_llm(user_msg):
    if not GROQ_API_KEY:
        return "AI chat is warming up. Please try again in a moment."
    try:
        import urllib.request
        payload = json.dumps({
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": f"You are an AI stock trading assistant for AI Market Cap scanner. The user asked: {user_msg}. Provide a helpful, concise response about pre-earnings momentum trading, stock analysis, or how to use the scanner."}]
        }).encode()
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=payload,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        return "I'm having trouble connecting right now. Please try again shortly."

@app.route("/logout")
def logout():
    resp = make_response(redirect("/"))
    resp.delete_cookie(COOKIE_NAME)
    resp.delete_cookie("stripe_customer")
    return resp

# ===== MAIN =====
if __name__ == "__main__":
    threading.Thread(target=auto_scan_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=PORT, debug=False)