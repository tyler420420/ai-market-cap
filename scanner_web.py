"""AI Earnings Scanner -- Web + Background Scanner Server (Railway Deploy)"""
import os, hashlib, secrets, time, subprocess, threading, sys, json, re
from pathlib import Path
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo
from flask import Flask, request, redirect, send_from_directory, abort, make_response, jsonify
import requests

# ===== CONFIG =====
PASSWORD_HASH = "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"
PASSWORD = os.environ.get("SCANNER_PASSWORD", "trading2026")
HTML_PATH = Path(__file__).parent / "ai_earnings_web.html"
SCANNER_PATH = Path(__file__).parent / "ai_earnings_scanner.py"
PORT = int(os.environ.get("PORT", 18766))
COOKIE_NAME = "scanner_session"
SESSION_TTL = 86400
PT = ZoneInfo("America/Los_Angeles")
AUTO_SCAN_HOUR = 6
AUTO_SCAN_MINUTE = 30

app = Flask(__name__)

# ===== SCAN STATE =====
class ScanState:
    scan_state = 'idle'
    refresh_state = 'idle'

scan_state = ScanState()
_last_auto_scan_date = None

# ===== PASSWORD AUTH =====
def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

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

def set_session(resp):
    token = make_session()
    resp.set_cookie(COOKIE_NAME, token, max_age=SESSION_TTL, httponly=True, samesite='Lax')

# ===== SCANNER CORE =====
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
    token = request.cookies.get(COOKIE_NAME, "")
    if validate_session(token):
        workspace = Path(__file__).parent
        html_files = sorted(workspace.glob("ai_earnings_57day_*.html"), key=lambda f: f.stat().st_mtime, reverse=True)
        if html_files:
            with open(html_files[0], 'r', encoding='utf-8') as f:
                content = f.read()
            resp = make_response(content)
            resp.headers['Content-Type'] = 'text/html; charset=utf-8'
            resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            return resp
        resp = make_response(send_from_directory(".", "ai_earnings_web.html"))
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        return resp
    return send_from_directory(".", "index.html")

@app.route("/scanner")
def scanner():
    token = request.cookies.get(COOKIE_NAME, "")
    if not validate_session(token):
        return redirect("/")
    workspace = Path(__file__).parent
    html_files = sorted(workspace.glob("ai_earnings_57day_*.html"), key=lambda f: f.stat().st_mtime, reverse=True)
    if html_files:
        with open(html_files[0], 'r', encoding='utf-8') as f:
            content = f.read()
        resp = make_response(content)
        resp.headers['Content-Type'] = 'text/html; charset=utf-8'
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        return resp
    # Fallback: serve static file with no-cache
    resp = make_response(send_from_directory(".", "ai_earnings_web.html"))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    return resp

@app.route("/login", methods=["POST"])
def login():
    pw = request.form.get("password", "")
    if pw == PASSWORD:
        resp = make_response(redirect("/scanner"))
        set_session(resp)
        return resp
    return send_from_directory(".", "index.html")

@app.route("/logout")
def logout():
    resp = make_response(redirect("/"))
    resp.delete_cookie(COOKIE_NAME)
    return resp

@app.route("/run", methods=["POST"])
def api_run():
    trigger_scan()
    return "ok"

@app.route("/status")
def api_status():
    return jsonify({
        'scan_state': scan_state.scan_state,
        'refresh_state': scan_state.refresh_state
    })

@app.route("/scan/latest")
def scan_latest():
    token = request.cookies.get(COOKIE_NAME, "")
    if not validate_session(token):
        abort(403)
    workspace = Path(__file__).parent
    html_files = sorted(workspace.glob("ai_earnings_57day_*.html"), key=lambda f: f.stat().st_mtime, reverse=True)
    if html_files:
        with open(html_files[0], 'r', encoding='utf-8') as f:
            return f.read(), 200, {"Content-Type": "text/html"}
    return "No scans yet", 404

@app.route("/api/chat", methods=["POST"])
def api_chat():
    token = request.cookies.get(COOKIE_NAME, "")
    if not validate_session(token):
        abort(403)
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
def scan_run():
    token = request.cookies.get(COOKIE_NAME, "")
    if not validate_session(token):
        abort(403)
    try:
        workspace = Path(__file__).parent
        result = subprocess.run(
            [sys.executable, str(SCANNER_PATH)],
            capture_output=True, text=True, timeout=180,
            cwd=str(workspace)
        )
        html_files = sorted(workspace.glob("ai_earnings_57day_*.html"), key=lambda f: f.stat().st_mtime, reverse=True)
        if html_files:
            with open(html_files[0], 'r', encoding='utf-8') as f:
                return f.read(), 200, {"Content-Type": "text/html"}
        return jsonify({"error": "Scan completed but no file found", "stdout": result.stdout, "stderr": result.stderr}), 500
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Scan timed out after 180s"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/run", methods=["OPTIONS"])
@app.route("/status", methods=["OPTIONS"])
def cors_preflight():
    resp = make_response("")
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return resp

# ===== LLM CHAT CONFIG =====
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL  = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE   = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")

SYSTEM_PROMPT = """You are the AI assistant for "AI Market Cap Scanner" — a pre-earnings momentum scanner for AI/AI-niche stocks.

CORE STRATEGY:
- Buy 1–14 days BEFORE earnings
- Sell 1–5 days AFTER a positive earnings beat
- Focus on stocks with high analyst ratings, high implied volatility (IV), and strong institutional backing

SCORING (composite score out of 100):
- Analyst coverage: 5–30 pts (20+ analysts = full 30 pts)
- Buy% (bullish ratings): up to 30 pts
- 5-day implied upside (options straddle × 5): up to 20 pts
- Strong Buy count (2 pts each): up to 20 pts

SCORE THRESHOLDS:
- 86+: Strong Buy (green) — best candidates
- 76–85: Watch (blue) — good, monitor closely
- 50–75: Caution (yellow) — marginal
- <50: Avoid (red)

COLUMNS:
- Score: composite rating 0–100
- PE Target: price target using 1× ATM straddle (conservative, 5–10% typical)
- 3-Day Momentum: straddle × 3 (mid-range upside)
- 5-Day Momentum: straddle × 5 (maximum upside shown)
- # of Analyst Signals: total analyst ratings covering this stock
- Strong Buy/Buy/Hold/Sell: breakdown of analyst ratings

HOW TO READ A TRADE:
- Look for Score 86+ (Strong Buy) with earnings in 1–10 days
- PE Target gives conservative exit price — sell here or slightly above after beat
- Never hold more than 5 days post-earnings regardless of outcome
- High IV stocks can move 10–30% on earnings beat

IMPORTANT: You are NOT a financial advisor. Always tell users to do their own research.
Answer questions clearly and concisely. Focus on how the scanner works, what the numbers mean, and trade strategy logic."""

def build_messages(user_input: str) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_input}
    ]

def call_llm(user_input: str) -> str:
    if not OPENAI_API_KEY:
        return "⚠️ Chat is not configured yet. The API key hasn't been set on the server."
    try:
        url = f"{OPENAI_BASE.rstrip('/')}/chat/completions"
        payload = {
            "model": OPENAI_MODEL,
            "messages": build_messages(user_input),
            "temperature": 0.7,
            "max_tokens": 400,
        }
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        choices = resp.json().get("choices", [])
        if choices:
            return choices[0]["message"]["content"].strip()
        return "No response from model."
    except requests.exceptions.Timeout:
        return "⏱️ Request timed out. Please try again."
    except Exception as e:
        return f"❌ Error: {str(e)}"

# ===== STARTUP =====
if __name__ == "__main__":
    auto_thread = threading.Thread(target=auto_scan_loop, daemon=True)
    auto_thread.start()
    print(f'[AI Market Cap] Auto-scan scheduler running ΓÇö next scan at 6:30 AM PT')
    print(f'[AI Market Cap] Web server ΓÇö http://0.0.0.0:{PORT}')
    print(f'[AI Market Cap] Password: {PASSWORD}')
    app.run(host="0.0.0.0", port=PORT, debug=False)
