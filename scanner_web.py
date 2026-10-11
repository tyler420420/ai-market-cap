"""AI Earnings Scanner -- Web + Background Scanner Server (Railway Deploy) v2"""
import os, hashlib, secrets, time, subprocess, threading, sys, json, re
from pathlib import Path
from datetime import datetime, time as dtime, timedelta
from zoneinfo import ZoneInfo
from flask import Flask, request, redirect, send_from_directory, abort, make_response, jsonify

# ===== STRIPE CONFIG =====
import stripe
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

# Price IDs from Stripe dashboard
PRICE_MONTHLY = "price_1UONSbQtzL43j3LF8GWzwl53"
PRICE_ANNUAL = "price_1UONTCQtzL43j3LF362d4eZl"

# ===== APP CONFIG =====
PORT = int(os.environ.get("PORT", 18766))
PT = ZoneInfo("America/Los_Angeles")
AUTO_SCAN_HOUR = 6
AUTO_SCAN_MINUTE = 30
COOKIE_NAME = "scanner_session"
SESSION_TTL = 86400

app = Flask(__name__, static_folder='static', static_url_path='/static')

# ===== HOME / SCANNER =====
# ===== PRO PICK CONFIG =====
PRO_PICK_FILE = Path(__file__).parent / "pro_pick.json"

def load_pro_pick():
    """Load today's Pro Pick from JSON file."""
    if PRO_PICK_FILE.exists():
        try:
            return json.loads(PRO_PICK_FILE.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None

def is_subscriber():
    """Check if current visitor has an active subscription."""
    customer_id = request.cookies.get("stripe_customer", "")
    if not customer_id:
        return False
    subs = get_subscriptions()
    return subs.get(customer_id, {}).get('status') == 'active'

@app.route("/api/pro_pick")
def api_pro_pick():
    """Return the Pro Pick only to active subscribers."""
    if not is_subscriber():
        return redirect("/pricing")
    pick = load_pro_pick()
    if not pick:
        return jsonify({"error": "No pick available today"}), 404
    return jsonify(pick)

@app.route("/pro")
def pro_dashboard():
    """Pro subscriber dashboard — exclusive AI Pick + top 5 ranked plays."""
    if not is_subscriber():
        return redirect("/pricing")

    pick = load_pro_pick()
    workspace = Path(__file__).parent
    primary = workspace / "ai_earnings_today.html"

    # Get top 5 stocks from the scanner data
    top5 = []
    if primary.exists():
        try:
            content = primary.read_text(encoding="utf-8")
            import re
            match = re.search(r'var rowsData\s*=\s*(\[.*?\]);', content, re.DOTALL)
            if match:
                top5 = json.loads(match.group(1))
                top5 = [r for r in top5 if r.get('score', 0) >= 80][:5]
        except Exception:
            pass

    today = datetime.now(PT).strftime("%B %d, %Y")
    pick_html = ""
    if pick:
        entry = pick.get('entry_price', 0)
        target = pick.get('target_price', 0)
        stop = pick.get('stop_loss', 0)
        upside = pick.get('upside_pct', 0)
        days = pick.get('days_to_earnings', '?')
        score = pick.get('score', 0)
        pick_html = f"""
        <div style="background:linear-gradient(135deg,#0d2b1a,#0a1f12);border:2px solid #2ea043;border-radius:16px;padding:40px;margin-bottom:30px;box-shadow:0 0 30px rgba(46,160,67,0.3)">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px">
                <span style="background:#2ea043;color:#fff;padding:4px 14px;border-radius:20px;font-size:0.75em;font-weight:bold;text-transform:uppercase">Pro Pick of the Day</span>
                <span style="color:#8b949e;font-size:0.85em">{today}</span>
            </div>
            <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;margin-bottom:24px">
                <div style="font-size:2.5em;font-weight:bold;color:#fff">{pick.get('ticker','')}</div>
                <div>
                    <div style="font-size:1.1em;color:#fff">{pick.get('company_name','')}</div>
                    <div style="font-size:0.85em;color:#8b949e">Score: <strong style="color:#2ea043">{score}</strong> · {pick.get('sector','')}</div>
                </div>
            </div>
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:16px;margin-bottom:24px">
                <div style="background:#0d1117;border-radius:10px;padding:16px;text-align:center">
                    <div style="color:#8b949e;font-size:0.75em;margin-bottom:4px">ENTRY PRICE</div>
                    <div style="color:#00ff88;font-size:1.5em;font-weight:bold">${int(entry)}</div>
                </div>
                <div style="background:#0d1117;border-radius:10px;padding:16px;text-align:center">
                    <div style="color:#8b949e;font-size:0.75em;margin-bottom:4px">TARGET</div>
                    <div style="color:#00ff88;font-size:1.5em;font-weight:bold">${int(target)}</div>
                </div>
                <div style="background:#0d1117;border-radius:10px;padding:16px;text-align:center">
                    <div style="color:#8b949e;font-size:0.75em;margin-bottom:4px">STOP LOSS</div>
                    <div style="color:#ff6b6b;font-size:1.5em;font-weight:bold">${int(stop)}</div>
                </div>
                <div style="background:#0d1117;border-radius:10px;padding:16px;text-align:center">
                    <div style="color:#8b949e;font-size:0.75em;margin-bottom:4px">UPSIDE</div>
                    <div style="color:#00ff88;font-size:1.5em;font-weight:bold">+{upside}%</div>
                </div>
                <div style="background:#0d1117;border-radius:10px;padding:16px;text-align:center">
                    <div style="color:#8b949e;font-size:0.75em;margin-bottom:4px">EARNINGS IN</div>
                    <div style="color:#ffd700;font-size:1.5em;font-weight:bold">{days}d</div>
                </div>
            </div>
            <div style="background:#0d1117;border-radius:10px;padding:20px;margin-bottom:20px">
                <div style="color:#8b949e;font-size:0.8em;margin-bottom:8px">WHY THIS PICK</div>
                <div style="color:#c9d1d9;font-size:0.95em;line-height:1.6">{pick.get('reasoning', 'High conviction pre-earnings momentum play. Strong analyst sentiment, optimal entry window.')}</div>
            </div>
            <a href="https://invite.kraken.com/JDNW/dq0q352v" target="_blank" style="display:inline-block;background:#5741d9;color:#fff;padding:14px 32px;border-radius:8px;font-weight:bold;text-decoration:none;font-size:1em">Trade {pick.get('ticker','')} on Kraken →</a>
        </div>"""
    else:
        pick_html = f"""
        <div style="background:#161b22;border:2px solid #30363d;border-radius:16px;padding:40px;margin-bottom:30px;text-align:center">
            <div style="font-size:1.2em;color:#fff;margin-bottom:10px">Pro Pick generating...</div>
            <div style="color:#8b949e;font-size:0.9em">Check back in a few minutes after the daily scan runs.</div>
        </div>"""

    # Top 5 ranked plays
    top5_html = ""
    if top5:
        cards = ""
        for r in top5:
            cards += f"""
            <div style="background:#161b22;border:1px solid #30363d;border-radius:10px;padding:20px">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
                    <div><strong style="color:#66b2ff;font-size:1.2em">{r['ticker']}</strong> <span style="color:#8b949e;font-size:0.85em">{r.get('company_name','')[:20]}</span></div>
                    <div style="background:rgba(46,160,67,0.2);color:#2ea043;padding:4px 12px;border-radius:20px;font-size:0.8em;font-weight:bold">Score {r['score']}</div>
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;font-size:0.82em">
                    <div><span style="color:#8b949e">Entry: </span><strong style="color:#fff">${int(r.get('price',0))}</strong></div>
                    <div><span style="color:#8b949e">Target: </span><strong style="color:#00ff88">${int(r.get('pe_target',0))}</strong></div>
                    <div><span style="color:#8b949e">Earnings: </span><strong style="color:#ffd700">{r.get('earnings_date','')[:12]}</strong></div>
                </div>
            </div>"""
        top5_html = f"""
        <h2 style="color:#fff;font-size:1.3em;margin-bottom:16px">Top 5 Ranked Pre-Earnings Plays</h2>
        <div style="display:grid;gap:12px;margin-bottom:30px">{cards}</div>"""

    dashboard_html = f"""<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" type="image/png" href="/static/logo.png">
<title>Pro Dashboard - AI Market Cap</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:Segoe UI,Arial,sans-serif;background:#0d1117;color:#c9d1d9;min-height:100vh}}
.header{{background:linear-gradient(135deg,#1a1f2e,#161b22);padding:20px 30px;border-bottom:1px solid #30363d;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px}}
.header h1{{color:#2ea043;font-size:1.5em}}
.header a{{color:#58a6ff;text-decoration:none;font-size:0.9em}}
.container{{max-width:900px;margin:0 auto;padding:40px 20px}}
h2{{color:#fff;font-size:1.3em;margin-bottom:16px;margin-top:40px}}
h2:first-child{{margin-top:0}}
.sub{{color:#8b949e;font-size:0.85em;margin-bottom:20px}}
.stats-row{{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:30px}}
.stat-box{{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:20px;flex:1;min-width:140px;text-align:center}}
.stat-box .val{{font-size:1.8em;font-weight:bold;color:#2ea043}}
.stat-box .lbl{{color:#8b949e;font-size:0.8em;margin-top:4px}}
.back-link{{display:inline-block;margin-top:30px;color:#58a6ff;text-decoration:none;font-size:0.9em}}
.back-link:hover{{color:#79b8ff}}
</style></head><body>
<div class=header>
    <h1>★ Pro Dashboard</h1>
    <div>
        <a href="/">← Scanner</a>
        <a href="/logout" style="margin-left:16px;color:#ff6b6b">Logout</a>
    </div>
</div>
<div class=container>
    <div class=sub>Your exclusive pre-earnings trade signals · Updated daily</div>
    <div class=stats-row>
        <div class=stat-box><div class=val>★</div><div class=lbl>Pro Pick of the Day</div></div>
        <div class=stat-box><div class=val>5</div><div class=lbl>Top Ranked Plays</div></div>
        <div class=stat-box><div class=val>$5</div><div class=lbl>/month · cancel anytime</div></div>
    </div>
    {pick_html}
    {top5_html}
    <a href="/" class=back-link>← Back to Scanner</a>
</div></body></html>"""
    return make_response(dashboard_html, 200, {"Content-Type": "text/html; charset=utf-8"})


@app.route("/")
def index():
    """Home page = scanner. ai_earnings_today.html is the primary file (always fresh from local scan).
    scanner.html is a legacy fallback only. Injects subscriber flag for gated AI Pick."""
    workspace = Path(__file__).parent
    # PRIMARY: ai_earnings_today.html — always fresh from local scan push
    primary = workspace / "ai_earnings_today.html"
    content = None
    if primary.exists():
        with open(primary, 'r', encoding='utf-8') as f:
            content = f.read()
    # LEGACY FALLBACK: scanner.html (only if ai_earnings_today.html is missing)
    if not content:
        shell = workspace / "scanner.html"
        if shell.exists():
            with open(shell, 'r', encoding='utf-8') as f:
                content = f.read()
    if not content:
        content = """
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
        </body></html>"""

    # Inject subscriber flag for gated AI Pick display
    subscriber_flag = "true" if is_subscriber() else "false"
    inject_script = f'<script>window.__isSubscriber={subscriber_flag};window.__proPickUrl="/api/pro_pick";</script>'
    # Inject right after <body> tag
    content = content.replace('<body>', '<body>' + inject_script, 1)

    resp = make_response(content)
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    return resp
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    return resp


# ===== SCANNER DATA (JSON) =====
@app.route("/data")
def data():
    """Serve scanner_data.json - fresh stock data for the static shell"""
    workspace = Path(__file__).parent
    json_file = workspace / "scanner_data.json"
    if json_file.exists():
        with open(json_file, 'r', encoding='utf-8') as f:
            content = f.read()
        resp = make_response(content)
        resp.headers['Content-Type'] = 'application/json; charset=utf-8'
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        return resp
    # Fallback: extract from ai_earnings_today.html
    today = workspace / "ai_earnings_today.html"
    if today.exists():
        with open(today, 'r', encoding='utf-8') as f:
            html = f.read()
        import re, json as _json
        m = re.search(r'var rowsData=(.*?);\s*var sortCol', html, re.DOTALL)
        if m:
            try:
                data = _json.loads(m.group(1))
                resp = make_response(_json.dumps(data))
                resp.headers['Content-Type'] = 'application/json; charset=utf-8'
                return resp
            except:
                pass
    return '{"error": "No data available"}', 404

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
                encoding='utf-8', errors='replace', timeout=600,
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

# ===== CRON STATE PERSISTENCE (survives Railway container restarts) =====
_CRON_STATE_FILE = Path(__file__).parent / ".cron_state.json"

def _load_cron_state():
    """Load cron run state from disk so it survives container restarts."""
    try:
        if _CRON_STATE_FILE.exists():
            with open(_CRON_STATE_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {"morning": None, "afternoon": None, "price_alerts": None}

def _save_cron_state(state):
    """Persist cron state to disk."""
    try:
        with open(_CRON_STATE_FILE, 'w') as f:
            json.dump(state, f)
    except Exception as e:
        print(f"[CronState] Failed to save: {e}")

# ===== AUTO SCAN CRON =====

@app.route("/cron")
def cron():
    """Triggered by Railway cron job at 6:30 AM PT daily"""
    now = datetime.now(PT)
    today = now.date()
    force = request.args.get('force') == '1'
    state = _load_cron_state()
    if not force and state.get("morning") == str(today):
        return "Already ran today", 200
    state["morning"] = str(today)
    _save_cron_state(state)

    def do_scan(label=""):
        """Railway cron: NEVER run the scanner (Railway can't do Finviz reliably).
        Only check freshness and serve existing data. Scanning happens locally."""
        today_path = Path(__file__).parent / "ai_earnings_today.html"
        if not today_path.exists():
            print(f"[Cron{label}] No data file — needs manual scan push")
            return False
        try:
            content = today_path.read_text(encoding='utf-8')
            stock_count = content.count('"ticker":')
            import re as _re
            data_date_match = _re.search(r'"ticker":\s*"([A-Z]+)".*?"earnings_date":\s*"([^"]+)".*?"days_left":\s*(\d+)', content, _re.DOTALL)
            if data_date_match:
                earn_str = data_date_match.group(2)
                days_left = int(data_date_match.group(3))
                try:
                    earn_dt = datetime.strptime(earn_str, '%B %d, %Y')
                    data_date = (earn_dt - timedelta(days=days_left)).date()
                    today_pt = datetime.now(PT).date()
                    if data_date == today_pt and stock_count >= 50:
                        print(f"[Cron{label}] Data FRESH — {data_date} == today {today_pt} ({stock_count} stocks)")
                        return True
                    else:
                        print(f"[Cron{label}] Data STALE — data date {data_date}, today {today_pt} ({stock_count} stocks). Needs manual scan.")
                        return False
                except Exception:
                    pass
            mtime = datetime.fromtimestamp(today_path.stat().st_mtime, tz=PT).date()
            if mtime == datetime.now(PT).date() and stock_count >= 50:
                print(f"[Cron{label}] Data FRESH (mtime {mtime}, {stock_count} stocks)")
                return True
            else:
                print(f"[Cron{label}] Data STALE — mtime {mtime}, {stock_count} stocks. Needs manual scan.")
                return False
        except Exception as e:
            print(f"[Cron{label}] Freshness check error: {e}")
            return False

    # Railway cron: never run scanner, just check freshness
    fresh = do_scan(label="[Morning]")
    if fresh:
        return f"Data fresh — {datetime.now(PT).date()} (auto-disabled scanner run)", 200
    else:
        return f"Data stale — run scanner locally and push. Cron scanner disabled.", 200


@app.route("/cron-afternoon")
def cron_afternoon():
    """Railway afternoon cron: only check freshness. Scanner runs locally."""
    now = datetime.now(PT)
    today = now.date()
    force = request.args.get('force') == '1'
    state = _load_cron_state()
    if not force and state.get("afternoon") == str(today):
        return "Already ran today", 200
    state["afternoon"] = str(today)
    _save_cron_state(state)

    today_path = Path(__file__).parent / "ai_earnings_today.html"
    if not today_path.exists():
        return "No data file — needs manual scan push", 200
    try:
        content = today_path.read_text(encoding='utf-8')
        stock_count = content.count('"ticker":')
        import re as _re
        m = _re.search(r'"ticker":\s*"([A-Z]+)".*?"earnings_date":\s*"([^"]+)".*?"days_left":\s*(\d+)', content, _re.DOTALL)
        if m:
            earn_dt = datetime.strptime(m.group(2), '%B %d, %Y')
            data_date = (earn_dt - timedelta(days=int(m.group(3)))).date()
            if data_date == today and stock_count >= 50:
                return f"Data fresh — afternoon check OK ({stock_count} stocks)", 200
        mtime = datetime.fromtimestamp(today_path.stat().st_mtime, tz=PT).date()
        if mtime == today and stock_count >= 50:
            return f"Data fresh — afternoon check OK ({stock_count} stocks)", 200
        return f"Data stale — run scanner locally and push", 200
    except Exception as e:
        return f"Check error: {e}", 200


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
    """Pricing page with Stripe Checkout — compelling, conversion-focused"""
    pricing_html = """<!DOCTYPE html>
<html><head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="icon" type="image/png" href="/static/logo.png">
    <meta name="description" content="Subscribe to AI Market Cap Pro — get the daily AI Pick, exclusive trade alerts, and the AI Chat Analyst for just $5/month.">
    <title>Pricing - AI Market Cap</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: Segoe UI, Arial, sans-serif; background: #0d1117; color: #c9d1d9; min-height: 100vh; }
.header { background: linear-gradient(135deg,#1a1f2e,#161b22); padding: 20px 30px; border-bottom: 1px solid #30363d; display: flex; justify-content: space-between; align-items: center; }
.header h1 { color: #58a6ff; font-size: 1.5em; }
.header a { color: #58a6ff; text-decoration: none; font-size: 0.9em; }
.container { max-width: 900px; margin: 0 auto; padding: 50px 20px; text-align: center; }
h2 { color: #fff; font-size: 2em; margin-bottom: 8px; }
.subtitle { color: #8b949e; font-size: 1em; margin-bottom: 40px; line-height: 1.6 }
.plans { display: flex; gap: 20px; justify-content: center; flex-wrap: wrap; }
.plan { background: #161b22; border: 1px solid #30363d; border-radius: 16px; padding: 32px; width: 280px; text-align: left; }
.plan.pro { border-color: #2ea043; box-shadow: 0 0 24px rgba(46,160,67,0.2); }
.plan h3 { color: #fff; font-size: 1.1em; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.05em }
.plan .price { font-size: 3em; font-weight: bold; color: #fff; margin-bottom: 4px; line-height: 1 }
.plan .price span { font-size: 0.35em; color: #8b949e; font-weight: normal; vertical-align: super }
.plan .period { color: #8b949e; font-size: 0.82em; margin-bottom: 24px; }
.plan .badge { display: inline-block; background: #2ea043; color: #fff; font-size: 0.7em; padding: 3px 10px; border-radius: 20px; margin-bottom: 12px; font-weight: bold }
.plan ul { list-style: none; margin-bottom: 28px; }
.plan li { color: #c9d1d9; font-size: 0.88em; padding: 7px 0; border-bottom: 1px solid #21262d }
.plan li:last-child { border-bottom: none }
.plan li::before { content: "✓ "; color: #2ea043; font-weight: bold }
.plan .cta { display: block; background: #2ea043; color: #fff; text-align: center; padding: 14px; border-radius: 10px; text-decoration: none; font-weight: bold; font-size: 1em; }
.plan .cta:hover { background: #3fb950; }
.plan.pro .cta { background: #2ea043; }
.plan.pro .cta:hover { background: #3fb950; }
.back-link { display: inline-block; margin-top: 40px; color: #58a6ff; text-decoration: none; font-size: 0.9em; }
.back-link:hover { color: #79b8ff; }
.testimonial { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 24px; margin-top: 40px; text-align: left; max-width: 500px; margin-left: auto; margin-right: auto }
.testimonial .stars { color: #ffd700; font-size: 1.1em; margin-bottom: 8px }
.testimonial .text { color: #c9d1d9; font-size: 0.9em; line-height: 1.6; font-style: italic; margin-bottom: 10px }
.testimonial .author { color: #8b949e; font-size: 0.8em }
</style></head><body>
<div class=header>
    <h1><a href="/" style="color:#58a6ff;text-decoration:none">AI Market Cap</a></h1>
    <a href="/">← Back to Scanner</a>
</div>

<div class=container>
    <h2>Your Daily AI Trade Alert — Yours for $5/mo</h2>
    <p class=subtitle>Get the Pro Pick of the Day with exact entry price, target, and stop loss.<br>Join traders who are getting ahead of earnings season.</p>
    <div class=plans>
        <div class="plan pro">
            <div class=badge>★ MOST POPULAR</div>
            <h3>Monthly</h3>
            <div class=price>$5<span>/mo</span></div>
            <div class=period>Billed monthly · cancel anytime</div>
            <ul>
                <li>Pro Pick of the Day — exact entry, target & stop</li>
                <li>Top 5 ranked pre-earnings plays</li>
                <li>Exclusive AI Chat Pro Trader</li>
                <li>Real-time earnings alerts</li>
                <li>Priority access before free users</li>
            </ul>
            <a href="/create-checkout?plan=monthly" class=cta>Start Pro — $5/month</a>
        </div>
        <div class=plan>
            <h3>Annual</h3>
            <div class=price>$50<span>/yr</span></div>
            <div class=period>~$4.17/month · save $10/year</div>
            <ul>
                <li>Everything in Monthly</li>
                <li>2 months free vs monthly</li>
                <li>Priority support</li>
            </ul>
            <a href="/create-checkout?plan=annual" class=cta>Subscribe - $50/yr</a>
        </div>
    </div>
    <div class=testimonial>
        <div class=stars>★★★★★</div>
        <div class=text>"This scanner helped me catch SNOW before earnings at $151 — it ran to $238 post-earnings. That's the kind of edge I'm looking for."</div>
        <div class=author>— Active trader, AI Market Cap member</div>
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

# ===== BLOG / ARTICLES =====
BLOG_DIR = Path(__file__).parent / "blog"

def load_blog_index():
    """Load the blog index manifest."""
    idx_path = BLOG_DIR / "index.json"
    if idx_path.exists():
        return json.loads(idx_path.read_text(encoding="utf-8"))
    return []

@app.route("/blog")
def blog_index():
    """Blog index — latest articles listing."""
    app_dir = Path(__file__).parent
    template_path = app_dir / "blog_index.html"
    
    # Try to use a custom blog index template if it exists
    if template_path.exists():
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        # Build from manifest
        articles = load_blog_index()
        cards_html = ""
        for a in articles[:6]:  # Latest 6
            cards_html += f"""<a href="/blog/{a['slug']}" class="win-card">
                <div class="h-badge" style="background:#1a3a5c;color:#58a6ff">📝 Article</div>
                <div class="t" style="color:#fff;font-size:1.1em;font-weight:bold;margin:8px 0 4px">{a['title']}</div>
                <div class="d" style="color:#888;font-size:0.82em;margin-bottom:8px">{a['date']} · {a.get('keyword', '')}</div>
                <div class="l" style="color:#c9d1d9;font-size:0.85em;line-height:1.6">{a.get('excerpt', '')}</div>
                <span class="link">Read article →</span>
            </a>"""
        
        if not cards_html:
            cards_html = "<p style='color:#888;text-align:center;padding:40px'>No articles yet. Check back soon.</p>"
        
        content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="icon" type="image/png" href="/static/logo.png">
<title>AI Market Cap — Articles</title>
<style>
a{{text-decoration:none;color:#58a6ff}}
a:hover{{color:#79b8ff}}
.w{{background:linear-gradient(135deg,#1a1f2e,#161b22);padding:20px 30px;border-bottom:1px solid #30363d;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px}}
.w h1 a{{color:#58a6ff;font-size:1.5em;text-decoration:none}}
.w .nav a{{margin-left:16px;color:#58a6ff;font-size:0.9em}}
.c{{max-width:960px;margin:0 auto;padding:40px 20px}}
h2{{color:#fff;font-size:1.9em;margin:0 0 8px}}
.sub{{color:#888;font-size:0.9em;margin-bottom:36px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:20px;margin:24px 0}}
.win-card{{display:block;background:#161b22;border:2px solid #30363d;border-radius:12px;padding:24px;transition:border-color .15s,transform .15s;text-decoration:none;color:inherit}}
.win-card:hover{{border-color:#1f6feb;transform:translateY(-2px)}}
.t{{font-size:1.15em;font-weight:bold;margin-bottom:6px}}
.d{{color:#888;font-size:0.82em;margin-bottom:12px}}
.l{{color:#c9d1d9;font-size:0.85em;line-height:1.6}}
.link{{color:#58a6ff;font-size:0.85em;font-weight:bold;display:inline-block;margin-top:12px}}
.h-badge{{display:inline-block;padding:4px 10px;border-radius:4px;font-size:0.72em;font-weight:bold;margin-bottom:8px}}
</style>
</head>
<body style="margin:0;padding:0;font-family:Segoe UI,Arial,sans-serif;background:#0d1117;color:#c9d1d9;min-height:100vh">
<div class=w>
  <h1><a href="/">AI Market Cap</a></h1>
  <div class=nav>
    <a href="/">Scanner</a>
    <a href="/wins">Wins</a>
    <a href="/blog" style="color:#ffd700;font-weight:bold">Blog</a>
    <a href="/about">About</a>
  </div>
</div>
<div class=c>
<h2>Latest Articles</h2>
<p class=sub>Daily AI stock analysis and pre-earnings insights.</p>
<div class=grid>
{cards_html}
</div>
</div>
</body>
</html>"""
    
    resp = make_response(content)
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    return resp

@app.route("/blog/<slug>")
def blog_article(slug):
    """Serve an individual blog article."""
    app_dir = Path(__file__).parent
    article_path = app_dir / "blog" / f"{slug}.html"

    if not article_path.exists():
        return "Article not found", 404

    with open(article_path, 'r', encoding='utf-8') as f:
        content = f.read()

    resp = make_response(content)
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    return resp

@app.route("/blog/index.json")
def blog_index_json():
    """Serve the blog article index as JSON."""
    articles = load_blog_index()
    resp = make_response(json.dumps(articles))
    resp.headers['Content-Type'] = 'application/json'
    return resp


@app.route("/sitemap.xml")
def sitemap():
    """XML sitemap for SEO — lists all static pages + blog articles."""
    articles = load_blog_index()
    base = "https://aismarketcap.com"

    # Static pages
    static_pages = [
        {"loc": f"{base}/", "priority": "1.0", "changefreq": "daily"},
        {"loc": f"{base}/wins", "priority": "0.8", "changefreq": "weekly"},
        {"loc": f"{base}/blog", "priority": "0.7", "changefreq": "daily"},
        {"loc": f"{base}/about", "priority": "0.6", "changefreq": "monthly"},
        {"loc": f"{base}/pricing", "priority": "0.9", "changefreq": "monthly"},
    ]

    # Individual wins pages
    wins_pages = []
    for f in Path(__file__).parent.glob("wins_*.html"):
        ticker = f.stem.replace("wins_", "")
        wins_pages.append({
            "loc": f"{base}/wins/{ticker}",
            "priority": "0.7",
            "changefreq": "monthly"
        })

    # Blog articles
    blog_items = [
        {
            "loc": f"{base}/blog/{a['slug']}",
            "priority": "0.6",
            "changefreq": "monthly",
            "lastmod": a.get("date", "")[:10]
        }
        for a in articles
    ]

    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    for page in static_pages + wins_pages + blog_items:
        lines.append("  <url>")
        lines.append(f"    <loc>{page['loc']}</loc>")
        if "lastmod" in page:
            lines.append(f"    <lastmod>{page['lastmod']}</lastmod>")
        lines.append(f"    <changefreq>{page['changefreq']}</changefreq>")
        lines.append(f"    <priority>{page['priority']}</priority>")
        lines.append("  </url>")

    lines.append("</urlset>")

    resp = make_response("\n".join(lines))
    resp.headers['Content-Type'] = 'application/xml'
    return resp

# ===== MANUAL SCAN TRIGGER (for force-updating the site) =====
@app.route("/trigger-scan")
def trigger_scan():
    """Manually run the scanner and update the site. Use ?key=SECRET to authenticate."""
    import os
    key = os.environ.get("SCAN_TRIGGER_KEY", "")
    provided = request.args.get("key", "")
    if key and provided != key:
        abort(403)
    now = datetime.now(PT)
    today_path = Path(__file__).parent / "ai_earnings_today.html"
    golden_path = Path(__file__).parent / "ai_earnings_golden.html"
    try:
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent / "ai_earnings_scanner.py")],
            capture_output=True, text=True,
            encoding='utf-8', errors='replace', timeout=180,
            cwd=str(Path(__file__).parent)
        )
        if today_path.exists():
            content = today_path.read_text(encoding='utf-8')
            stock_count = content.count('"ticker":')
            json_idx = content.find('var rowsData=')
            json_len = 0
            if json_idx >= 0:
                arr_depth, json_end = 0, json_idx
                for i in range(json_idx + 12, len(content)):
                    ch = content[i]
                    if ch == '[': arr_depth += 1
                    elif ch == ']':
                        arr_depth -= 1
                        if arr_depth == 0:
                            json_end = i
                            json_len = json_end - (json_idx + 12) + 1
                            break
            if json_len >= 5000 and stock_count >= 5:
                import shutil
                shutil.copy2(today_path, golden_path)
                return f"Scan OK: {stock_count} stocks, rowsData={json_len} bytes", 200
            else:
                return f"Scan invalid: {stock_count} stocks, rowsData={json_len} bytes (need 5000+ bytes, 5+ stocks)", 500
        return f"Scan failed: no output file", 500
    except Exception as e:
        return f"Scan error: {e}", 500

# ===== TRAFFIC DASHBOARD =====
TRAFFIC_DIR = Path(r"C:\Users\Tyler_AI\Desktop\traffic_machine")

@app.route("/traffic")
def traffic_dashboard():
    """Serve the Traffic Machine Master Control dashboard."""
    dashboard_path = TRAFFIC_DIR / "traffic_dashboard.html"
    if not dashboard_path.exists():
        return "Dashboard not found.", 404
    return send_from_directory(str(TRAFFIC_DIR), "traffic_dashboard.html")

@app.route("/traffic/state.json")
def traffic_state():
    """Serve the Traffic Machine state for the dashboard."""
    state_file = TRAFFIC_DIR / "traffic_machine_state.json"
    if not state_file.exists():
        return jsonify({"articles_published": {}, "social_posts": {}, "outreach_sent": {}, "last_run": None})
    return send_from_directory(str(TRAFFIC_DIR), "traffic_machine_state.json")

@app.route("/traffic/backlinks_state.json")
def traffic_backlinks_state():
    """Serve comment backlinks state for the dashboard."""
    cb_file = TRAFFIC_DIR / "comment_backlinks_state.json"
    if not cb_file.exists():
        return jsonify({"stats": {"total": 0, "success": 0, "failed": 0}, "commented_urls": [], "daily_runs": []})
    return send_from_directory(str(TRAFFIC_DIR), "comment_backlinks_state.json")

@app.route("/traffic/syndication_state.json")
def traffic_syndication_state():
    """Serve content syndication state for the dashboard."""
    synd_file = TRAFFIC_DIR / "syndication_state.json"
    if not synd_file.exists():
        return jsonify({"daily_runs": [], "articles": {}})
    return send_from_directory(str(TRAFFIC_DIR), "syndication_state.json")

@app.route("/traffic/niche_backlinks_state.json")
def traffic_niche_backlinks_state():
    """Serve niche backlinks state for the dashboard."""
    nb_file = TRAFFIC_DIR / "niche_backlinks_state.json"
    if not nb_file.exists():
        return jsonify({
            "daily_runs": [], "guest_posts": [],
            "quora_posts": [], "comment_urls": [],
            "stats": {"total": 0, "live": 0, "pending": 0, "failed": 0}
        })
    return send_from_directory(str(TRAFFIC_DIR), "niche_backlinks_state.json")

@app.route("/traffic/config.json")
def traffic_config_status():
    """Serve config status (which platforms are configured) for the dashboard."""
    import yaml
    config_file = TRAFFIC_DIR / "config.yaml"
    if not config_file.exists():
        return jsonify({})
    with open(config_file, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    g = cfg.get("global", {})
    clients_raw = cfg.get("clients", {})
    clients_out = {}
    for name, c in clients_raw.items():
        # Build platform list — only show what's actually connected
        raw_plats = c.get("platforms", {})
        plats = {}
        # Twitter — connected if API key set
        if g.get("twitter_api_key") and "twitter" in raw_plats:
            plats["twitter"] = raw_plats["twitter"]
        # Email outreach — connected if Gmail configured
        if g.get("gmail_from") and g.get("gmail_app_password") and "email_outreach" in raw_plats:
            plats["email_outreach"] = raw_plats["email_outreach"]
        # Comment backlinks — always available
        if "comment_backlinks" in raw_plats:
            plats["comment_backlinks"] = raw_plats["comment_backlinks"]
        # Bing — always available (sitemap ping free)
        if "bing" in raw_plats:
            plats["bing"] = raw_plats["bing"]
        # Google — always available (sitemap ping free)
        plats["google"] = {"enabled": True}
        # Bluesky — connected if handle set globally
        if g.get("bluesky", {}).get("handle") and "bluesky" in raw_plats:
            plats["bluesky"] = raw_plats["bluesky"]
        # Mastodon — connected if access token set globally
        if g.get("mastodon", {}).get("access_token") and "mastodon" in raw_plats:
            plats["mastodon"] = raw_plats["mastodon"]
        # Quora — connected if email set in client config
        if "quora" in raw_plats and raw_plats["quora"].get("email"):
            plats["quora"] = raw_plats["quora"]
        # Skip reddit & linkedin — require API approval, not currently connected

        clients_out[name] = {
            "url": c.get("wp_url", ""),
            "niche": c.get("site_niche", ""),
            "site_type": c.get("site_type", "wordpress"),
            "enabled": c.get("enabled", False),
            "platforms": plats,
        }
    # Check if any client has Quora configured
    has_quora = any(
        bool(c.get("platforms", {}).get("quora", {}).get("email"))
        for c in clients_raw.values()
    )
    return jsonify({
        "hasReddit": bool(g.get("reddit", {}).get("client_id")),
        "hasLinkedIn": bool(g.get("linkedin", {}).get("access_token")),
        "hasBing": True,  # Sitemap ping works free, no key needed
        "hasGSC": bool(g.get("gsc_service_account_json")),
        "hasEmail": bool(g.get("gmail_from") and g.get("gmail_app_password")),
        "hasTwitter": bool(g.get("twitter_api_key")),
        "hasBluesky": bool(g.get("bluesky", {}).get("handle")),
        "hasMastodon": bool(g.get("mastodon", {}).get("access_token")),
        "hasQuora": has_quora,
        "hasCommentBacklinks": True,  # Built-in, no API key needed
        "clients": clients_out,
    })

@app.route("/traffic/queue")
def traffic_queue():
    """List queued articles (pending, not yet published)."""
    queue_dir = TRAFFIC_DIR / "article_queue"
    items = []
    if queue_dir.exists():
        for f in queue_dir.glob("aismarketcap_*.json"):
            items.append({
                "name": f.name,
                "date": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                "client": "aismarketcap",
                "type": "wins" if "_wins" in f.name else "daily"
            })
    items.sort(key=lambda x: x["date"], reverse=True)
    return jsonify(items[:20])


@app.route("/traffic/new-client")
def traffic_new_client_page():
    """Serve the Add New Client wizard page."""
    wizard_path = TRAFFIC_DIR / "new_client.html"
    if not wizard_path.exists():
        return "Wizard not found.", 404
    return send_from_directory(str(TRAFFIC_DIR), "new_client.html")


@app.route("/traffic/add-client", methods=["POST"])
def traffic_add_client():
    """Add a new client to config.yaml."""
    try:
        data = request.get_json()
        client_name = data.get("client_name", "").strip().lower()
        site_url = data.get("site_url", "").strip().rstrip("/")
        site_niche = data.get("site_niche", "").strip()
        site_type = data.get("site_type", "flask_blog")
        author = data.get("author", "").strip() or client_name.replace("-", " ").title()
        platforms_cfg = data.get("platforms", {})

        if not client_name or not site_url or not site_niche:
            return jsonify({"ok": False, "error": "Missing required fields"}), 400

        import re
        if not re.match(r"^[a-z0-9][a-z0-9\-]*$", client_name):
            return jsonify({"ok": False, "error": "Invalid client slug"}), 400

        config_file = TRAFFIC_DIR / "config.yaml"
        with open(config_file, "r", encoding="utf-8") as f:
            config_text = f.read()

        seo_articles_enabled = platforms_cfg.get('seo_articles', True)
        # Build client YAML block
        client_block = f"""
  {client_name}:
    enabled: true
    wp_url: "{site_url}"
    site_url: "{site_url}"
    site_niche: "{site_niche}"
    site_type: "{site_type}"
    author: "{author}"
    client_name: "{client_name}"
    seo_articles: {str(seo_articles_enabled).lower()}
    blog_git_dir: ""   # Set for Flask blog clients, e.g. C:/Users/Tyler_AI/ai-market-cap/blog
    platforms:
      twitter:
        enabled: {str(platforms_cfg.get('twitter', True)).lower()}
        handle: "@AIMoneyMach"
      reddit:
        enabled: false
        subreddits: []
      linkedin:
        enabled: false
        company_urn: ""
      bing:
        enabled: {str(platforms_cfg.get('bing', True)).lower()}
        sitemap_url: "{site_url}/sitemap.xml"
      email_outreach:
        enabled: {str(platforms_cfg.get('email_outreach', True)).lower()}
        outreach_targets:
          - "finance"
          - "investing"
          - "technology"
      comment_backlinks:
        enabled: {str(platforms_cfg.get('comment_backlinks', True)).lower()}
        max_per_article: 25
        min_da: 20
      mastodon:
        enabled: {str(platforms_cfg.get('mastodon', True)).lower()}
      bluesky:
        enabled: {str(platforms_cfg.get('bluesky', False)).lower()}
"""

        # Append before the last blank line or end of file
        if "clients:" in config_text:
            lines = config_text.split("\n")
            insert_idx = len(lines)
            for i, line in enumerate(lines):
                if line.strip().startswith("report_") or (line.strip() == "..." and i > len(lines) - 10):
                    insert_idx = i
                    break
            lines.insert(insert_idx, client_block.lstrip("\n"))
            config_text = "\n".join(lines)

        with open(config_file, "w", encoding="utf-8") as f:
            f.write(config_text)

        return jsonify({"ok": True, "client": client_name})
    except Exception as e:
        import traceback
        return jsonify({"ok": False, "error": str(e), "trace": traceback.format_exc()}), 500


@app.route("/traffic/report/<client>")
def traffic_report(client):
    """Generate a full analytics report for a client — opens in new tab."""
    try:
        sys.path.insert(0, str(TRAFFIC_DIR))
        from generate_report import make_report
        html = make_report(client)
        return html, 200, {"Content-Type": "text/html; charset=utf-8"}
    except Exception:
        import traceback
        return f"<pre>Report error:\n{traceback.format_exc()}</pre>", 500
def traffic_outreach():
    """Serve outreach state for the dashboard."""
    state_file = TRAFFIC_DIR / "modules" / "outreach_state.json"
    fallback = TRAFFIC_DIR / "outreach_state.json"
    src = state_file if state_file.exists() else fallback
    if not src.exists():
        return jsonify({"sent": [], "replied": [], "bounced": [], "last_run": None})
    with open(src, encoding="utf-8") as f:
        return jsonify(json.load(f))

@app.route("/traffic/action-log")
def traffic_action_log():
    """Read the last action log output."""
    log_path = TRAFFIC_DIR / "traffic_action.log"
    if not log_path.exists():
        return jsonify({"log": ""})
    content = log_path.read_text(encoding="utf-8")
    # Return last 3000 chars
    return jsonify({"log": content[-3000:]})

@app.route("/traffic/action", methods=["POST"])
def traffic_action():
    """
    Launch any Traffic Machine action.
    - Wizard/setup scripts: open in a new terminal window so Tyler can interact with them
    - Publish/report scripts: run hidden, capture output to a live log file
    """
    import subprocess
    import threading

    data = request.get_json(silent=True) or {}
    action = data.get("action", "")
    client = data.get("client", "")
    python_exe = sys.executable

    # Scripts that need an interactive terminal (wizards)
    interactive_scripts = {
        "reddit_setup", "bing_setup", "linkedin_setup", "bluesky_setup", "mastodon_setup",
    }

    action_map = {
        "reddit_setup":     (str(TRAFFIC_DIR / "reddit_setup.py"),       []),
        "bing_setup":       (str(TRAFFIC_DIR / "bing_setup.py"),         []),
        "linkedin_setup":   (str(TRAFFIC_DIR / "linkedin_poster.py"),   ["--setup"]),
        "email_setup":      (str(TRAFFIC_DIR / "email_setup.py"),        []),
        "bluesky_setup":    (str(TRAFFIC_DIR / "modules" / "bluesky_poster.py"), ["--setup"]),
        "mastodon_setup":   (str(TRAFFIC_DIR / "modules" / "mastodon_poster.py"), ["--setup"]),
        "new_client":       (str(TRAFFIC_DIR / "master_setup_wizard.py"), []),
        "publish":          (str(TRAFFIC_DIR / "traffic_engine.py"),     ["--publish"]),
        "run_full":         (str(TRAFFIC_DIR / "traffic_engine.py"),     []),    # generate + publish
        "run_outreach":     (str(TRAFFIC_DIR / "traffic_engine.py"),     ["--outreach"]),
        "report_all":       (str(TRAFFIC_DIR / "client_report.py"),     []),
        "run_client":       (str(TRAFFIC_DIR / "traffic_engine.py"),     ["--client", client, "--publish"]) if client else None,
        "report_client":    (str(TRAFFIC_DIR / "client_report.py"),     ["--client", client]) if client else None,
    }

    if action not in action_map:
        return jsonify({"error": "Unknown action", "available": list(action_map.keys())}), 400

    entry = action_map[action]
    if entry is None:
        return jsonify({"error": "client name required"}), 400

    script_path, extra_args = entry

    def run_hidden():
        """Run silently, append output to a live log file."""
        log_path = TRAFFIC_DIR / "traffic_action.log"
        with open(log_path, "a", encoding="utf-8") as logf:
            logf.write(f"\n{'='*50}\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ACTION: {action} | CLIENT: {client or 'all'}\n{'='*50}\n")
            logf.flush()
            try:
                result = subprocess.run(
                    [python_exe, script_path] + extra_args,
                    cwd=str(TRAFFIC_DIR),
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if result.stdout:
                    logf.write(result.stdout)
                if result.stderr:
                    logf.write("STDERR:\n" + result.stderr)
                logf.write(f"\n[EXIT CODE: {result.returncode}]\n")
            except subprocess.TimeoutExpired:
                logf.write("[TIMEOUT: 120s exceeded]\n")
            except Exception as e:
                logf.write(f"[ERROR: {e}]\n")

    if action in interactive_scripts:
        # Open in a new terminal window for interactive input
        cmd_str = 'start "Traffic Machine" cmd /k cd /d "{}" && {} "{}" {}'.format(
            TRAFFIC_DIR, python_exe, script_path, ' '.join(extra_args)
        )
        try:
            subprocess.Popen(cmd_str, shell=True, cwd=str(TRAFFIC_DIR))
            return jsonify({"ok": True, "action": action, "mode": "interactive"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        # Run silently in background, log to file
        threading.Thread(target=run_hidden, daemon=True).start()
        return jsonify({"ok": True, "action": action, "client": client or None})

# ===== MAIN =====
if __name__ == "__main__":
    @app.route("/push", methods=["GET", "POST"])
    def push_html():
        """Push scanner_data.json and regenerate ai_earnings_today.html"""
        token = os.environ.get("PUSH_TOKEN", "tyler_secret_token")
        if request.args.get("token") != token:
            return "Unauthorized", 401
        base = Path(__file__).parent
        if request.method == "GET":
            json_path = base / "scanner_data.json"
            if json_path.exists():
                content = json_path.read_text(encoding="utf-8")
                idx = content.find('"NXPI"')
                n = content[idx:idx+150] if idx >= 0 else "NXPI not found"
                return f"NXPI: {n}", 200
            return "File not found", 404
        data = request.get_data(as_text=True)
        if not data or len(data) < 100:
            return "Content too short", 400
        # Detect HTML vs JSON
        if data.strip().startswith("<"):
            # HTML content - write to scanner.html and ai_earnings_today.html
            html_path = base / "ai_earnings_today.html"
            scanner_path = base / "scanner.html"
            html_path.write_text(data, encoding="utf-8")
            scanner_path.write_text(data, encoding="utf-8")
            return f"Written HTML: {len(data)} bytes to both files", 200
        # JSON content
        json_path = base / "scanner_data.json"
        json_path.write_text(data, encoding="utf-8")
        # Regenerate HTML from JSON
        try:
            import json as _json
            jdata = _json.loads(data)
            if isinstance(jdata, list):
                rows = jdata
            elif isinstance(jdata, dict):
                rows = jdata.get("stocks", jdata.get("data", []))
            else:
                rows = []
            if rows:
                sys.path.insert(0, str(base))
                from ai_earnings_scanner import generate_html_report
                html_path = base / "ai_earnings_today.html"
                scanner_path = base / "scanner.html"
                generate_html_report(rows, str(html_path))
                generate_html_report(rows, str(scanner_path))
                return f"Written JSON ({len(data)} bytes) + HTML regenerated", 200
        except Exception as e:
            return f"Written JSON ({len(data)} bytes), HTML regen failed: {e}", 200
        return f"Written JSON: {len(data)} bytes", 200

    threading.Thread(target=auto_scan_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=PORT, debug=False)