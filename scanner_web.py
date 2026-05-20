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

app = Flask(__name__)

# ===== SCAN STATE =====
class ScanState:
    scan_state = 'idle'
    refresh_state = 'idle'

scan_state = ScanState()
_last_auto_scan_date = None

# ===== SUBSCRIPTION MANAGEMENT =====
# Simple file-based subscription store (for demo - use DB in production)
SUBS_FILE = Path(__file__).parent / "subscriptions.json"

def get_subscriptions():
    if SUBS_FILE.exists():
        try:
            return json.loads(SUBS_FILE.read_text())
        except:
            return {}
    return {}

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
    try:
        result = subprocess.run(
            [sys.executable, str(SCANNER_PATH)],
            capture_output=True, text=True,
            encoding='utf-8', errors='replace', timeout=180,
            cwd=str(Path(__file__).parent)
        )
        print('[Scanner] Full scan complete. Exit code:', result.returncode)
        scan_state.scan_state = 'done'
    except Exception as e:
        print('[Scanner] Scan error:', e)
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

# ===== WEB ROUTES =====

@app.route("/")
def index():
    """Home page = scanner (no login required)"""
    workspace = Path(__file__).parent
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
        <p>Scanner is warming up. Check back in a few minutes.</p>
        <a href="/pricing" class=btn>Subscribe to Unlock Full Access</a>
    </body></html>""")
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    return resp

@app.route("/about")
def about():
    """Original landing page"""
    return send_from_directory(".", "index.html")

@app.route("/pricing")
def pricing():
    """Pricing page with Stripe Checkout"""
    pricing_html = """<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
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
.plan.featured .cta { background: linear-gradient(135deg,#2a1a00,#ffd700); color: #fff; }
.plan.featured .cta:hover { background: linear-gradient(135deg,#3a2000,#ffe033); }
.back-link { display: inline-block; margin-top: 40px; color: #58a6ff; text-decoration: none; font-size: 0.9em; }
.back-link:hover { color: #79b8ff; }
</style></head><body>
<div class=header>
    <h1>AI Market Cap</h1>
    <a href="/">View Scanner</a>
</div>
<div class=container>
    <h2>Unlock Full Access</h2>
    <p class=subtitle>Get unlimited daily scans, real-time prices, and AI-powered trade picks.</p>
    <div class=plans>
        <div class=plan>
            <h3>Monthly</h3>
            <div class=price>$149<span>/mo</span></div>
            <div class=period>Billed monthly</div>
            <ul>
                <li>All AI stocks monitored</li>
                <li>Score + PE/3D/5D targets</li>
                <li>AI Suggested Trade</li>
                <li>Live price ticker</li>
                <li>News per stock</li>
                <li>Auto-scan at 6:30 AM PT daily</li>
            </ul>
            <a href="/create-checkout?plan=monthly" class=cta>Subscribe - $149/mo</a>
        </div>
        <div class="plan featured">
            <h3>Annual</h3>
            <div class=price>$999<span>/yr</span></div>
            <div class=period>Save $789 vs monthly</div>
            <ul>
                <li>Everything in Monthly</li>
                <li>Unlimited daily scans</li>
                <li>Early access to new features</li>
                <li>Priority support</li>
                <li>Save $789/year</li>
            </ul>
            <a href="/create-checkout?plan=annual" class=cta>Subscribe - $999/yr</a>
        </div>
    </div>
    <a href="/about" class=back-link>← Learn more about AI Market Cap</a>
</div>
</body></html>"""
    return make_response(pricing_html, 200, {"Content-Type": "text/html; charset=utf-8"})

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
        return make_response(success_html, 200, {"Content-Type": "text/html; charset=utf-8"})
    except Exception as e:
        return f"Error: {e}", 500

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
    """Run scan - requires active subscription"""
    token = request.cookies.get(COOKIE_NAME, "")
    customer_id = request.cookies.get("stripe_customer", "")

    # Check subscription
    subs = get_subscriptions()
    is_active = subs.get(customer_id, {}).get('status') == 'active' or subs.get(token, {}).get('status') == 'active'

    if not is_active:
        return redirect("/pricing")

    trigger_scan()
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
        return jsonify({"error": "subscription_required", "redirect": "/pricing"}), 403

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