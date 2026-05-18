"""Background server for the AI Earnings Scanner.
Handles /run (full scan), /status, and auto-runs at 6:30 AM PT daily."""
import http.server, threading, subprocess, os, sys, time, re
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo

PORT = 18765
SCANNER_PATH = r"C:\Users\Tyler_AI\.mavis\sessions\mvs_41a119d03ae849d59a2cdecd57e77d10\workspace\ai_earnings_scanner.py"
WORKSPACE = r"C:\Users\Tyler_AI\.mavis\sessions\mvs_41a119d03ae849d59a2cdecd57e77d10\workspace"
PT = ZoneInfo("America/Los_Angeles")

# Auto-scan time: 6:30 AM Pacific
AUTO_SCAN_HOUR = 6
AUTO_SCAN_MINUTE = 30


class ScanState:
    scan_state = 'idle'   # idle / running / done
    refresh_state = 'idle' # idle / running / done


scan_state = ScanState()
_last_auto_scan_date = None


class Handler(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        if self.path == '/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            import json
            self.wfile.write(json.dumps({
                'scan_state': scan_state.scan_state,
                'refresh_state': scan_state.refresh_state
            }).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/run':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'ok')
            _trigger_scan()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, fmt, *args):
        pass


def _trigger_scan():
    scan_state.scan_state = 'running'
    scan_state.refresh_state = 'idle'
    print('[Scanner Server] Scan triggered.')
    t = threading.Thread(target=_run_full_scan, daemon=True)
    t.start()


def _run_full_scan():
    try:
        result = subprocess.run(
            [sys.executable, SCANNER_PATH],
            capture_output=True, text=True,
            encoding='utf-8', errors='replace', timeout=180,
            cwd=WORKSPACE
        )
        print('[Scanner Server] Full scan complete. Exit code:', result.returncode)
        scan_state.scan_state = 'done'
    except Exception as e:
        print('[Scanner Server] Scan error:', e)
        scan_state.scan_state = 'done'


def _auto_scan_loop():
    global _last_auto_scan_date
    while True:
        now_pt = datetime.now(PT)
        today_date = now_pt.date()
        target = datetime.combine(today_date, dtime(AUTO_SCAN_HOUR, AUTO_SCAN_MINUTE), tzinfo=PT)

        # If it's already past 6:30 AM, schedule for tomorrow
        if now_pt >= target:
            try:
                target = datetime.combine(today_date.replace(day=today_date.day + 1), dtime(AUTO_SCAN_HOUR, AUTO_SCAN_MINUTE), tzinfo=PT)
            except ValueError:
                # Day out of range — advance to next month
                target = datetime.combine(today_date.replace(month=today_date.month + 1, day=1), dtime(AUTO_SCAN_HOUR, AUTO_SCAN_MINUTE), tzinfo=PT)

        wait_seconds = (target - now_pt).total_seconds()
        print(f'[Auto-Scan] Next scan at {target.strftime("%Y-%m-%d %I:%M %p PT")} (in {wait_seconds/3600:.1f} hrs)')
        time.sleep(wait_seconds)

        # Only run once per day
        if datetime.now(PT).date() != _last_auto_scan_date:
            _trigger_scan()
            _last_auto_scan_date = datetime.now(PT).date()


def run_server():
    server = http.server.HTTPServer(('', PORT), Handler)
    print(f'[Scanner Server] Running on http://localhost:{PORT}')
    print(f'[Scanner Server] /run = full scan | /status = check state')
    server.serve_forever()


if __name__ == '__main__':
    import http.client
    try:
        c = http.client.HTTPConnection('localhost', PORT, timeout=1)
        c.request('GET', '/status')
        c.getresponse()
        print('Server already running on port', PORT)
        sys.exit(0)
    except:
        pass

    # Start auto-scan scheduler in background thread
    auto_thread = threading.Thread(target=_auto_scan_loop, daemon=True)
    auto_thread.start()
    print('[Auto-Scan] Daily scan scheduler started — runs at 6:30 AM PT every day.')

    run_server()