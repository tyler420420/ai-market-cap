"""AI Earnings Scanner — Web + Background Scanner Server (Railway Deploy)"""
import os, hashlib, secrets, time, subprocess, threading, sys
from pathlib import Path
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo
from flask import Flask, request, redirect, send_from_directory, abort, make_response, jsonify

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
    try:
        # Run an initial scan on boot so the scanner has data immediately
        print('[Auto-Scan] Running initial scan on startup...')
        trigger_scan()
    except Exception as e:
        print('[Auto-Scan] Initial scan error:', e)
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
    if not validate_session(token):
        return send_from_directory(".", "login.html")
    workspace = Path(__file__).parent
    html_files = sorted(workspace.glob("ai_earnings_57day_*.html"), key=lambda f: f.stat().st_mtime, reverse=True)
    if html_files:
        with open(html_files[0], 'r', encoding='utf-8') as f:
            content = f.read()
        resp = make_response(content)
        resp.headers['Content-Type'] = 'text/html; charset=utf-8'
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return resp
    return send_from_directory(".", "ai_earnings_web.html")

@app.route("/login", methods=["POST"])
def login():
    pw = request.form.get("password", "")
    if pw == PASSWORD:
        resp = make_response(redirect("/"))
        set_session(resp)
        return resp
    return send_from_directory(".", "login.html")

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
    html_files = sorted(workspace.glob("ai_earnings_57day_*.html"), reverse=True)
    if html_files:
        with open(html_files[0], 'r', encoding='utf-8') as f:
            return f.read(), 200, {"Content-Type": "text/html"}
    return "No scans yet", 404

@app.route("/scan/run", methods=["POST"])
def scan_run():
    """Run a fresh scan and return the new HTML"""
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
        html_files = sorted(workspace.glob("ai_earnings_57day_*.html"), reverse=True)
        if html_files:
            with open(html_files[0], 'r', encoding='utf-8') as f:
                return f.read(), 200, {"Content-Type": "text/html"}
        return jsonify({"error": "Scan completed but no file found", "stdout": result.stdout, "stderr": result.stderr}), 500
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Scan timed out after 180s"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===== CORS preflight =====
@app.route("/run", methods=["OPTIONS"])
@app.route("/status", methods=["OPTIONS"])
def cors_preflight():
    resp = make_response("")
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return resp

# ===== STARTUP =====
if __name__ == "__main__":
    # Start auto-scan scheduler
    auto_thread = threading.Thread(target=auto_scan_loop, daemon=True)
    auto_thread.start()
    print(f'[AI Market Cap] Auto-scan scheduler running — next scan at 6:30 AM PT')
    print(f'[AI Market Cap] Web server — http://0.0.0.0:{PORT}')
    print(f'[AI Market Cap] Password: {PASSWORD}')
    app.run(host="0.0.0.0", port=PORT, debug=False)