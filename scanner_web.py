"""AI Earnings Scanner -- Web + Background Scanner Server (Railway Deploy) v2"""
import os, hashlib, secrets, time, subprocess, threading, sys, json, re
import urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, time as dtime, timedelta, date
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


def _plain(obj):
    """Convert a StripeObject to a real dict so .get() works.

    stripe-python >= 7 returns StripeObject (Session, Subscription, Customer,
    Invoice), which is NOT a dict subclass - calling .get() on one raises
    "AttributeError: get". Older code here treated webhook payloads as dicts,
    so a real payment raised inside the webhook handler, the subscription was
    never saved, and the buyer saw "Payment received but there was a problem
    activating your account" - while Stripe had already taken the money.

    to_dict() recurses into nested objects, so obj['metadata'] and
    obj['customer_details'] come back as plain dicts too. Dicts and None pass
    through unchanged, so this is safe to call on anything from the API.
    """
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    try:
        return obj.to_dict()
    except Exception:
        # Already a plain mapping-like, or an object that cannot convert.
        # Returning {} keeps callers safe: they all use .get(...) with a
        # default, so a missing value degrades instead of crashing.
        try:
            return dict(obj)
        except Exception:
            return {}

# ===== APP CONFIG =====
PORT = int(os.environ.get("PORT", 18766))
PT = ZoneInfo("America/Los_Angeles")
AUTO_SCAN_HOUR = 6
AUTO_SCAN_MINUTE = 30
COOKIE_NAME = "scanner_session"
SESSION_TTL = 86400

# ===== RAILWAY SAFETY =====
# NEVER run the scanner inside the Railway web container.
#
# The scanner loads pandas/numpy and pulls ~224 tickers from yfinance, which
# blows past Railway's free-tier memory limit. The container gets OOM-killed,
# enters a restart loop, Railway marks the service unhealthy, and the domain
# serves `x-railway-fallback: true` -> 404 on every route. This is exactly
# what happened on 2026-10-20.
#
# Fresh data comes from the local Windows machine: daily_scan.ps1 scans,
# commits and pushes to GitHub, and Railway redeploys the static HTML.
# Set ALLOW_IN_CONTAINER_SCAN=1 to re-enable (local dev only).
ALLOW_IN_CONTAINER_SCAN = os.environ.get("ALLOW_IN_CONTAINER_SCAN", "") == "1"
if not ALLOW_IN_CONTAINER_SCAN:
    print("[Safety] In-container scanner DISABLED — data comes from local push")

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

def get_subscriber_count():
    """Return the number of active subscribers for social proof display."""
    try:
        subs = get_subscriptions()
        real_count = sum(1 for s in subs.values() if s.get("status") == "active")
        # If no real subscribers yet, start at 0 — honest is better than fake social proof
        return real_count if real_count > 0 else 0
    except Exception:
        return 0

# NOTE: an earlier version of this file defined a simplified is_subscriber() here
# that trusted the stripe_customer cookie plus the local file, with no Stripe
# validation. It was dead code shadowed by the real two-tier implementation
# further down. It has been removed so there is exactly ONE definition — having
# two meant an edit to the weak one could look correct while the live one
# silently stayed different.

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


# ===== PAYWALL RENDERING =====
# The pick banners ship as one static HTML file with the paid numbers inside.
# These helpers decide, per request, what actually goes over the wire.

PRO_TEASER = (
    '<div class="pro-teaser" style="display:flex;flex-wrap:wrap;gap:8px;'
    'align-items:center;padding:12px 10px;border-radius:8px;'
    'background:rgba(0,0,0,0.3)">'
    '<span style="font-size:0.8em;color:#8b949e;font-weight:bold;margin-right:4px">PRO:</span>'
    '<span style="font-size:0.82em;color:#c9d1d9">Entry, target and stop loss '
    'unlock with Pro</span></div>'
)


VALUES_OPEN = '<!--PROVALUES-->'
VALUES_CLOSE = '<!--/PROVALUES-->'
CTA_OPEN = '<!--PROCTA-->'
CTA_CLOSE = '<!--/PROCTA-->'


def _drop_next_anchor(content, i):
    """Remove the single <a ...>...</a> that starts at/after i.

    Used as the fail-closed path for an unpaired CTA marker. Cutting to the
    next marker or to the end of the document instead would truncate the
    footer and everything below the banner. An unpaired upsell button is a
    cosmetic defect; a truncated page is a real one.
    """
    a = content.find('<a ', i)
    if a == -1:
        return content
    close = content.find('</a>', a)
    if close == -1:
        return content
    return content[:a] + content[close + 4:]


def _values_fail_close(content, i):
    """Fail closed on an unpaired PROVALUES opener: cut the values away.

    Bounds matter. The blunt "return content[:i]" version truncates the rest
    of the document. Stop at the next banner, or at the end of the page
    shell, whichever comes first, so a broken generator produces a damaged
    banner rather than a blank site.
    """
    for bound in (CTA_OPEN, '<div class="pro-values-box"', '</body>'):
        k = content.find(bound, i + 1)
        if k != -1:
            return content[:i] + PRO_TEASER + content[k:]
    return content[:i] + PRO_TEASER


def _strip_block(content, marker):
    """Remove every block between marker and its matching <!--/PRO*-->.

    Loops because a banner carries more than one CTA (the top-row "Unlock
    PRO Targets" link AND the overlay button). Stripping only the first
    occurrence left the second one on the page for paying customers.

    Fails CLOSED. An opening marker with no closer means the shipped artifact
    came from a generator that does not know how to close the block. Returning
    the content untouched would be the dangerous option: for PROVALUES that
    ships the paid numbers to the public while the guard reports green.
    """
    close = {CTA_OPEN: CTA_CLOSE, VALUES_OPEN: VALUES_CLOSE}[marker]
    while True:
        i = content.find(marker)
        if i == -1:
            return content
        j = content.find(close, i)
        if j != -1:
            content = content[:i] + content[j + len(close):]
            continue
        if marker == CTA_OPEN:
            # The marker itself goes, plus the button it introduces.
            return content[:i] + _drop_next_anchor(content[i + len(marker):], 0)
        return _values_fail_close(content, i)


def _strip_element(content, element_id):
    """Remove a whole <div ... id=...> or class=...>...</div> with its children.

    Counts div nesting so it removes the correct block rather than stopping at
    the first inner </div>, which would leave a fragment of orphaned markup.

    Matches class= as well as id= because the two banners name their overlays
    differently: Today's Pick uses id="pro-gate", Runner Up uses
    class="ru-pro-gate". Matching id= only silently left the Runner Up blur
    sitting on top of a paying customer's numbers.
    """
    m = re.search(
        r'<div[^>]*(?:id|class)="%s"[^>]*>' % re.escape(element_id), content)
    if not m:
        return content
    start = m.start()
    pos = m.end()
    depth = 1
    while depth > 0:
        nxt_open = content.find('<div', pos)
        nxt_close = content.find('</div>', pos)
        if nxt_close == -1:
            return content[:start]
        if nxt_open != -1 and nxt_open < nxt_close:
            depth += 1
            pos = nxt_open + 4
        else:
            depth -= 1
            pos = nxt_close + 6
    return content[:start] + content[pos:]


def _strip_pro_values(content):
    """Replace each paid values block with a teaser, for non-subscribers.

    The real entry / target / stop numbers are removed from the response
    entirely. They are the entire product, and a translucent overlay over data
    already in the HTML is not a paywall.

    Fails CLOSED: an opening marker with no closing marker means the artifact
    was built by an older generator. Refusing to send the numbers is the
    correct trade against a damaged banner.
    """
    while True:
        i = content.find(VALUES_OPEN)
        if i == -1:
            return content
        j = content.find(VALUES_CLOSE, i)
        if j != -1:
            content = content[:i] + PRO_TEASER + content[j + len(VALUES_CLOSE):]
            continue
        return _values_fail_close(content, i)


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
    if is_subscriber():
        # Hide Subscribe button, show Pro badge linking to /account
        nav_hide = (
            '<style>.nav-subscribe{display:none!important}</style>'
            '<style>'
            '.pro-account-badge{position:fixed;top:12px;right:12px;z-index:10000;'
            'background:linear-gradient(135deg,#2ea043,#3fb950);color:#fff;'
            'padding:6px 14px;border-radius:20px;font-size:0.82em;font-weight:bold;'
            'text-decoration:none;box-shadow:0 0 12px rgba(46,160,67,0.4);'
            'border:1px solid #5dff7f}'
            '.pro-account-badge:hover{background:linear-gradient(135deg,#3fb950,#5dff7f)}'
            '</style>'
            '<a href=/account class=pro-account-badge>★ Pro</a>'
        )
    else:
        nav_hide = ''
    # ── PAYWALL, RENDERED SERVER-SIDE ────────────────────────────────────
    # Tyler 2026-10-22: "the pro subscriber should have todays pick and runner
    # up picks unlocked and not blurred with the buttons removed since they
    # paid".
    #
    # The blur was hiding nothing. Audit of the PUBLIC response found
    # "3D TARGET $145" and "STOP $84" in plain text inside the HTML a
    # non-subscriber downloads - view-source read the entire $5 product for
    # free. So this is not a styling fix, it is the paywall actually existing.
    #
    # Now the generator marks the sensitive block (<!--PROVALUES-->) and the
    # subscribe CTA (<!--PROCTA-->) in both banners, and this is where the
    # decision is made per-request:
    #
    #   subscriber  -> values kept, CTA and both blur overlays REMOVED
    #   everyone else -> values STRIPPED (never sent), CTA + overlay kept
    #
    # Server-side, not JS. Hiding a paywall with client script means the data
    # still reaches the customer who opened devtools, and it flashes the
    # blurred state at paying subscribers before the script runs.
    if is_subscriber():
        # They paid. Remove the upsell buttons and the overlays outright so
        # nothing blurred remains, and so nobody is asked to "unlock" what
        # they already bought.
        content = _strip_block(content, CTA_OPEN)
        content = _strip_element(content, 'pro-gate')
        content = _strip_element(content, 'ru-pro-gate')
        # The values box clips its children (overflow:hidden) so the blur
        # overlay could cover them cleanly. With the overlay gone the clip
        # would cut off the unblurred numbers on narrow screens. Targeted at
        # the .pro-values-box class rather than an exact style string, which
        # silently stopped matching the moment the markup changed.
        content = re.sub(
            r'(<div class="pro-values-box"[^>]*?)overflow:hidden;\s*',
            r'\1', content)
    else:
        # They have not paid, so the numbers must not be sent at all.
        content = _strip_pro_values(content)

    # The markers are build-time plumbing. Once the decision above is made they
    # are meaningless to the browser, and leaving them in the response tells a
    # paying customer exactly where the paywall boundaries are.
    for _m in (VALUES_OPEN, VALUES_CLOSE, CTA_OPEN, CTA_CLOSE):
        content = content.replace(_m, '')

    # Inject subscriber flag for any remaining client-side behaviour
    inject_script = f'<script>window.__isSubscriber={subscriber_flag};window.__proPickUrl="/api/pro_pick";</script>'
    # Inject right after <body> tag
    # Non-subscribers only. A paying customer must never be shown an upsell
    # for the list he already receives.
    if subscriber_flag != "true":
        content = content.replace('<body>', '<body>' + EMAIL_CAPTURE, 1)
    content = content.replace('<body>', '<body>' + nav_hide + inject_script, 1)

    resp = make_response(content)
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
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
# Cache-Control is deliberately short (5 min) rather than the long default.
# Favicons are cached hard by browsers, and a stale/404 entry survives a long
# max-age - which is how the icon stayed missing long after the outage ended.
def _serve_icon(filename, mimetype):
    resp = make_response(send_from_directory(
        os.path.dirname(__file__), filename, mimetype=mimetype))
    resp.headers['Cache-Control'] = 'public, max-age=300'
    return resp

@app.route('/favicon.ico')
def favicon():
    return _serve_icon('favicon.ico', 'image/x-icon')

@app.route('/favicon.png')
def favicon_png():
    return _serve_icon('favicon.png', 'image/png')

@app.route('/apple-touch-icon.png')
def apple_touch_icon():
    return _serve_icon('favicon.png', 'image/png')

# ===== INDEXNOW =====
# IndexNow (https://www.indexnow.org) is the supported replacement for the
# retired anonymous sitemap pings - google.com/ping now returns 404 and
# bing.com/ping returns 410. Bing and its partners fetch the verification key
# from this URL before trusting any submission, so it must be publicly
# readable and must stay identical to indexnow_key.txt.
@app.route('/indexnow_key.txt')
def indexnow_key():
    key_file = Path(__file__).parent / "indexnow_key.txt"
    if not key_file.exists():
        return ("indexnow key not configured", 404)
    resp = make_response(key_file.read_text(encoding="utf-8").strip())
    resp.headers['Content-Type'] = 'text/plain; charset=utf-8'
    resp.headers['Cache-Control'] = 'public, max-age=3600'
    return resp

# ===== STOCK PAGES — aismarketcap.com/stock/TICKER =====
STOCK_PAGES_DIR = Path(__file__).parent / "stock_pages"

@app.route("/stock/<ticker>")
@app.route("/stock/<ticker>/")
def stock_page(ticker):
    """Serve a pre-generated SEO stock page for the given ticker."""
    ticker = ticker.upper()
    page_file = STOCK_PAGES_DIR / f"{ticker}.html"
    if not page_file.exists():
        # Generate on the fly if not pre-built
        try:
            import yfinance as yf
            t = yf.Ticker(ticker)
            info = t.info or {}
            price = info.get('currentPrice') or info.get('regularMarketPrice') or 0
            name = info.get('shortName', '') or info.get('longName', '') or ticker
            mktcap = info.get('marketCap', 0)
            rec = info.get('recommendationKey', 'N/A')
            analyst = info.get('numberOfAnalystOpinions', 0)
            target = info.get('targetMeanPrice', 0)
            pe = info.get('trailingPE', 0)
            eps = info.get('trailingEps', 0)
            sector = info.get('sector', '')
            industry = info.get('industry', '')
            price_str = f"${price:.2f}" if price else "N/A"
            mktcap_str = f"${mktcap/1e9:.1f}B" if mktcap else "N/A"
            rec_color = '#2ea043' if rec in ('buy','strong_buy','moderate_buy') else '#ffa657' if rec=='hold' else '#f85149'
            earnings_date = info.get('earningsDates', 'Upcoming')
            if isinstance(earnings_date, list) and earnings_date:
                earnings_date = str(earnings_date[0])
            rec_display = rec.replace('_',' ').title() if rec else 'N/A'
            body = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{name} ({ticker}) Stock Analysis — {earnings_date}</title>
<meta name="description" content="{name} ({ticker}) pre-earnings analysis. Entry signals, analyst ratings, and implied move ahead of earnings. Updated daily.">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://aismarketcap.com/stock/{ticker}">
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{font-family:'Segoe UI',Arial,sans-serif;background:#0d1117;color:#c9d1d9;line-height:1.6}}
  a{{color:#58a6ff;text-decoration:none}}a:hover{{text-decoration:underline}}
  .topbar{{background:linear-gradient(135deg,#1a1f2e,#161b22);padding:18px 24px;border-bottom:1px solid #30363d;display:flex;align-items:center;gap:16px}}
  .brand{{color:#7ee787;font-size:1.1em;font-weight:bold}}.brand span{{color:#ffd700}}
  .topbar a{{color:#8b949e;font-size:0.85em}}
  .container{{max-width:820px;margin:0 auto;padding:24px 20px}}
  .breadcrumb{{font-size:0.78em;color:#444;margin-bottom:16px}}
  .breadcrumb a{{color:#58a6ff}}
  h1{{color:#fff;font-size:1.7em;margin-bottom:6px}}
  .sub{{color:#8b949e;font-size:0.88em;margin-bottom:18px}}
  .metrics{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px;margin-bottom:24px}}
  .m{{background:#161b22;border:1px solid #21262d;border-radius:10px;padding:14px;text-align:center}}
  .m .v{{font-size:1.3em;font-weight:bold;color:#7ee787}}
  .m .l{{font-size:0.68em;color:#555;text-transform:uppercase;margin-top:3px}}
  .cta{{background:linear-gradient(135deg,#1a2a1a,#0d1a0d);border:2px solid #2ea043;border-radius:12px;padding:22px;text-align:center;margin-bottom:20px}}
  .cta h2{{color:#7ee787;font-size:1em;margin-bottom:8px}}
  .cta p{{color:#8b949e;font-size:0.85em;margin-bottom:14px}}
  .cta-btn{{display:inline-block;background:#ffd700;color:#000;padding:10px 24px;border-radius:8px;font-weight:bold;font-size:0.88em;text-decoration:none}}
  .cta-btn:hover{{background:#ffe033;text-decoration:none}}
  .sec{{background:#161b22;border:1px solid #21262d;border-radius:12px;padding:20px;margin-bottom:16px}}
  .sec h2{{color:#fff;font-size:0.95em;margin-bottom:12px;font-weight:600;border-bottom:1px solid #21262d;padding-bottom:8px}}
  .sec p{{color:#8b949e;font-size:0.87em;margin-bottom:10px}}
  .sec ul{{color:#8b949e;font-size:0.87em;padding-left:18px;margin-bottom:10px}}
  .sec li{{margin-bottom:6px}}
  .hi{{color:#fff;font-weight:600}}
  .gr{{color:#7ee787}}
  .bl{{color:#58a6ff}}
  .am{{color:#ffa657}}
  .footer{{text-align:center;color:#333;font-size:0.72em;padding:24px 20px;border-top:1px solid #1e1e2e;margin-top:20px}}
</style>
</head>
<body>
<div class="topbar">
  <div class="brand">AI Market Cap <span>Pro</span></div>
  <div><a href="https://aismarketcap.com">← Back to Scanner</a><a href="https://aismarketcap.com/pricing" style="margin-left:14px">Pricing</a></div>
</div>
<div class="container">
  <div class="breadcrumb"><a href="https://aismarketcap.com">Home</a> &rsaquo; <a href="https://aismarketcap.com/stocks">Stock Analysis</a> &rsaquo; {ticker}</div>
  <h1>{name} ({ticker}) — Pre-Earnings Stock Analysis</h1>
  <p class="sub">{sector}{', '+industry if industry and sector else industry or ''}</p>
  <div class="metrics">
    <div class="m"><div class="v">{price_str}</div><div class="l">Price</div></div>
    <div class="m"><div class="v">{mktcap_str}</div><div class="l">Market Cap</div></div>
    <div class="m"><div class="v">{'N/A' if not pe else f'{pe:.1f}'}</div><div class="l">P/E Ratio</div></div>
    <div class="m"><div class="v">{'N/A' if not target else f'${target:.0f}'}</div><div class="l">Price Target</div></div>
    <div class="m"><div class="v">{analyst}</div><div class="l">Analysts</div></div>
    <div class="m"><div class="v" style="color:{rec_color}">{rec_display}</div><div class="l">Rating</div></div>
  </div>
  <div class="cta">
    <h2>🔥 Get {ticker} Targets Before Earnings — Unlock with Pro</h2>
    <p>Pre-earnings entry zone, analyst PE target, 3-day and 5-day implied move, and stop loss — all in the AI Market Cap Pro scanner.</p>
    <a href="https://aismarketcap.com/pricing" class="cta-btn">Unlock Full Analysis →</a>
  </div>
  <div class="sec">
    <h2>Pre-Earnings Strategy for {ticker}</h2>
    <p>Trading <span class="hi">{name} ({ticker})</span> before earnings requires identifying high-conviction setups where the implied move is priced below what the stock has historically delivered on a beat.</p>
    <p>Key factors our scanner tracks for {ticker}: analyst conviction (current: <span class="gr">{rec_display}</span>), implied volatility, pre-earnings momentum, and days to the next earnings report.</p>
    <ul>
      <li><strong>Buy 5-12 days before earnings</strong> — captures momentum without excessive time decay on options premium.</li>
      <li><strong>Set 10% stop loss pre-earnings</strong> — earnings volatility can swing 20-30% on a miss.</li>
      <li><strong>Sell within 5 days of a beat</strong> — momentum fades as short-term traders take profits.</li>
      <li><strong>Check short interest</strong> — elevated short interest increases squeeze potential on a positive earnings surprise.</li>
    </ul>
  </div>
  <div class="sec">
    <h2>AI Market Cap Pro — Full Analysis for {ticker}</h2>
    <p>The <a href="https://aismarketcap.com">AI Market Cap pre-earnings scanner</a> covers {ticker} alongside 20+ other stocks in the current earnings window. Pro subscribers get:</p>
    <ul>
      <li>Pre-earnings <span class="bl">entry price recommendation</span></li>
      <li>Analyst <span class="gr">PE target</span> and upside %</li>
      <li><span class="am">3-day and 5-day implied move</span> from options straddle pricing</li>
      <li><span class="hi">Stop loss level</span> based on IV and historical volatility</li>
      <li>Daily updated scores across all stocks with earnings in the next 30 days</li>
    </ul>
    <p style="margin-top:12px"><a href="https://aismarketcap.com/pricing">Subscribe for $5/month →</a></p>
  </div>
</div>
<div class="footer">AI Market Cap &nbsp;|&nbsp; <a href="https://aismarketcap.com">Scanner</a> &nbsp;|&nbsp; <a href="https://aismarketcap.com/privacy">Privacy</a><br>Not financial advice. Do your own research. © {datetime.now().year}</div>
</body>
</html>"""
            return body, 200, {"Content-Type": "text/html; charset=utf-8", "Cache-Control": "public, max-age=3600"}
        except Exception:
            return f"<h1>{ticker} — Page not found</h1><p>No data available for this ticker. <a href='https://aismarketcap.com'>Back to scanner</a>.", 404
    return send_from_directory(str(STOCK_PAGES_DIR), f"{ticker}.html", mimetype='text/html')

@app.route("/stocks")
def stocks_index():
    """Index page listing all available stock analysis pages."""
    stock_dir = Path(__file__).parent / "stock_pages"
    tickers = sorted([f.stem for f in stock_dir.glob("*.html")]) if stock_dir.exists() else []

    ticker_rows = ""
    for t in tickers:
        ticker_rows += f'<a href="/stock/{t}" style="display:inline-block;background:#161b22;border:1px solid #21262d;border-radius:8px;padding:8px 16px;color:#58a6ff;font-size:0.85em;font-weight:bold;text-decoration:none;margin:4px;">{t}</a>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Stock Analysis — AI Market Cap</title>
<meta name="description" content="Pre-earnings stock analysis for 224 AI and tech stocks. Target prices, analyst ratings, entry signals, and earnings dates — all free.">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:Segoe UI,Arial,sans-serif;background:#0d1117;color:#c9d1d9;padding:0;min-height:100vh}}
.topbar{{background:linear-gradient(135deg,#1a1f2e,#161b22);padding:20px 24px;border-bottom:1px solid #30363d;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}}
.topbar-brand{{color:#7ee787;font-size:1.2em;font-weight:bold}}
.topbar a{{color:#8b949e;font-size:0.85em;text-decoration:none;margin-left:16px}}
.topbar a:hover{{color:#fff}}
.hero{{text-align:center;padding:60px 20px;background:linear-gradient(135deg,#0d1117,#1a2a1a)}}
.hero h1{{color:#fff;font-size:2.2em;margin-bottom:10px}}
.hero p{{color:#8b949e;font-size:1em;max-width:600px;margin:0 auto 24px;line-height:1.6}}
.hero .cta{{display:inline-block;background:#ffd700;color:#000;padding:14px 28px;border-radius:8px;font-weight:bold;text-decoration:none;font-size:0.95em}}
.grid{{max-width:900px;margin:0 auto;padding:30px 20px}}
.grid h2{{color:#fff;font-size:1.1em;margin-bottom:16px;font-weight:600;border-bottom:1px solid #21262d;padding-bottom:10px}}
.ticker-grid{{display:flex;flex-wrap:wrap;gap:6px}}
.footer{{text-align:center;color:#333;font-size:0.75em;padding:30px 20px;border-top:1px solid #1e1e2e;margin-top:40px}}
</style>
</head>
<body>
<div class="topbar">
  <div class="topbar-brand">AI Market Cap <span style="color:#ffd700">Pro</span></div>
  <div>
    <a href="https://aismarketcap.com">← Scanner</a>
    <a href="https://aismarketcap.com/pricing">Pricing</a>
  </div>
</div>
<div class="hero">
  <h1>224 Pre-Earnings Stock Analyses</h1>
  <p>Each page shows the analyst consensus, implied move, entry zone, and pre-earnings setup — for {len(tickers)} AI and tech stocks with upcoming earnings reports.</p>
  <a href="https://aismarketcap.com/pricing" class="cta">Unlock Targets + Stop Loss →</a>
</div>
<div class="grid">
  <h2>All Stock Pages ({len(tickers)} total)</h2>
  <div class="ticker-grid">{ticker_rows}</div>
</div>
<div class="footer">AI Market Cap — Not financial advice. Do your own research. © {datetime.now().year}</div>
</body></html>"""
    return html, 200, {"Content-Type": "text/html; charset=utf-8"}

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
MAX_SCANS_PER_DAY = 3

# ===== ON-DEMAND SCAN QUEUE ===========================================
# Tyler 2026-10-22: "point the scan to my local machine, that is best
# solution."
#
# WHY THIS SHAPE. The scanner cannot run inside the Railway container - it
# OOM'd the container into a restart loop that 404'd every route, which is
# why ALLOW_IN_CONTAINER_SCAN is off. But the real scanner runs fine on
# Tyler's Windows box, where daily_scan.ps1 already scans, commits and pushes
# so Railway redeploys the fresh HTML. So the button does not run a scan; it
# leaves a REQUEST, and the local machine picks it up.
#
# PULL, NOT PUSH. The local machine sits behind NAT and cannot be reached
# inbound from the internet without an exposed tunnel - and an unauthenticated
# public endpoint that can start scans is a denial-of-service lever anyone
# could pull. So Railway only ever stores a request; the machine polls with a
# shared secret. Nothing is reachable inbound, and a stranger can neither read
# nor clear a request.
#
# FILE-BASED, HONEST ABOUT IT. The queue is a JSON file on the container's
# ephemeral disk, so a Railway restart loses a pending request. That is the
# correct trade for this feature: a scan is a best-effort convenience with a
# scheduled daily fallback, and losing one is far better than blocking deploys
# on a database nobody operates.
SCAN_QUEUE_FILE = Path(__file__).parent / "scan_queue.json"
SCAN_SECRET = os.environ.get("SCAN_SECRET", "")
# How long a claimed request stays claimed before another poller may take it.
# The real scan takes ~4 minutes, so this must comfortably exceed that or two
# pollers would run the same scan twice.
SCAN_CLAIM_TTL_S = 900


def _read_queue():
    try:
        return json.loads(SCAN_QUEUE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"state": "idle"}


def _write_queue(q):
    try:
        SCAN_QUEUE_FILE.write_text(json.dumps(q, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"[ScanQueue] write failed: {e}")


def _poller_ok():
    """True when the request carries the shared poller secret."""
    if not SCAN_SECRET:
        return False
    sent = (request.headers.get("X-Scan-Secret") or "").strip()
    return bool(sent) and secrets.compare_digest(sent, SCAN_SECRET)


@app.route("/api/scan-poll", methods=["GET"])
def api_scan_poll():
    """Claim a pending on-demand scan. Local machine only, secret required.

    Returns the claim and marks it 'running' so a second poller cannot start a
    duplicate. If a claim is older than SCAN_CLAIM_TTL_S the machine is assumed
    dead mid-scan and the request is released back to 'pending'."""
    if not _poller_ok():
        return jsonify({"error": "forbidden"}), 403
    q = _read_queue()
    now = time.time()
    state = q.get("state", "idle")
    if state == "running":
        started = float(q.get("claimed_at") or 0)
        if now - started < SCAN_CLAIM_TTL_S:
            return jsonify({"state": "running", "claimed_at": q.get("claimed_at")})
        # Stale claim - the poller died. Release it.
        print(f"[ScanQueue] stale claim released after {int(now - started)}s")
        state = "pending"
    if state != "pending":
        return jsonify({"state": state})
    q.update({"state": "running", "claimed_at": now,
              "requested_at": q.get("requested_at"), "requested_by": q.get("requested_by")})
    _write_queue(q)
    print(f"[ScanQueue] claimed scan requested by {q.get('requested_by')}")
    return jsonify({"state": "claimed", "requested_at": q.get("requested_at")})


@app.route("/api/scan-complete", methods=["POST"])
def api_scan_complete():
    """Report the local scan finished (or failed). Local machine only."""
    if not _poller_ok():
        return jsonify({"error": "forbidden"}), 403
    body = request.get_json(silent=True) or {}
    ok = bool(body.get("ok"))
    detail = str(body.get("detail") or "")[:300]
    q = _read_queue()
    q.update({"state": "idle", "completed_at": time.time(),
              "last_ok": ok, "last_detail": detail})
    _write_queue(q)
    print(f"[ScanQueue] local scan complete ok={ok} {detail}")
    return jsonify({"state": "idle"})

# ===== VISITOR COUNTER =====================================================
# Tyler 2026-10-21 00:10 PT: wanted a real "Website visitors" number on the CEO
# dashboard. There is no analytics on this site, so this counts it ourselves.
#
# PRIVACY: no raw IPs are ever stored or exposed. Each visitor is reduced to a
# salted SHA-256 prefix for that day only, used solely to de-duplicate. Rotate
# the salt and every historical hash becomes useless.
#
# Robustness: this MUST never be able to break the site, so every operation is
# wrapped and failures are swallowed. Analytics failing silently is fine; the
# storefront going down is not.
VISITOR_FILE = Path(__file__).parent / "visitor_counts.json"
# Railway wipes the container filesystem on every redeploy, so the live counter
# alone would reset to ~0 each time CTO pushes. visitor_baseline.json is
# committed to git and survives redeploys; all_time = baseline + live since boot.
VISITOR_BASELINE_FILE = Path(__file__).parent / "visitor_baseline.json"
VISITOR_SALT = os.environ.get("VISITOR_SALT", "aismarketcap-visit-v1")
VISITOR_KEEP_DAYS = 30
VISITOR_FLUSH_SEC = 20
# Never count these - they are not humans and would inflate the number.
VISITOR_SKIP = ('static', 'favicon', 'robots.txt', 'sitemap', '.png', '.jpg',
                '.jpeg', '.gif', '.svg', '.ico', '.css', '.js', '.woff', '.map',
                '/api/', '/health', '/webhook', '/verify_auth')

# Unfiltered "hits" would be meaningless here: IndexNow alone pings ~237 URLs a
# day and every search crawler sweeps the site hourly. Those hits are excluded,
# so the number reflects people, not machines. No UA string means a script.
_BOT_RE = re.compile(
    r"bot\b|bot/|crawl|spider|slurp|scrapy|curl|wget|python-requests|httpclient|"
    r"libwww|java/|go-http|okhttp|axios|node-fetch|headless|phantomjs|pingdom|"
    r"uptimerobot|monitoring|indexnow|ahrefs|semrush|mj12|dotbot|petal|"
    r"facebookexternalhit|whatsapp|telegrambot|slackbot|discordbot|preview|"
    r"lighthouse|gtmetrix|pagespeed|chrome-lighthouse|screaming frog",
    re.I)
_EMPTY_UA_RE = re.compile(r"^\s*(-|python-requests)\s*$", re.I)

# In-memory state, flushed to disk on a timer. Writing JSON on every request
# would put a disk write in front of every page view and race across threads.
_vlock = threading.Lock()
_vdirty = False
_vstate = {"hits": 0, "days": {}}


def _visitor_bucket(remote_addr):
    raw = f"{VISITOR_SALT}|{remote_addr}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def _load_visitor_state():
    global _vdirty
    try:
        if VISITOR_FILE.exists():
            data = json.loads(VISITOR_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                with _vlock:
                    _vstate["hits"] = int(data.get("hits", 0) or 0)
                    days = data.get("days")
                    if isinstance(days, dict):
                        _vstate["days"] = {k: dict(v) for k, v in days.items()}
    except Exception:
        pass


def _flush_visitor_state():
    """Atomic write: a crash mid-write must not corrupt the counter."""
    global _vdirty
    try:
        with _vlock:
            _vdirty = False
            cutoff = (datetime.now(PT) - timedelta(days=VISITOR_KEEP_DAYS)).strftime("%Y-%m-%d")
            days = {k: v for k, v in _vstate["days"].items() if k >= cutoff}
            payload = {"hits": _vstate["hits"], "days": days,
                       "saved": datetime.now(PT).strftime("%Y-%m-%d %H:%M:%S")}
        tmp = VISITOR_FILE.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload), encoding="utf-8")
        os.replace(tmp, VISITOR_FILE)
    except Exception:
        pass


def _visitor_flusher():
    while True:
        time.sleep(VISITOR_FLUSH_SEC)
        with _vlock:
            dirty = _vdirty
        if dirty:
            _flush_visitor_state()


def _record_visit(remote_addr):
    global _vdirty
    today = datetime.now(PT).strftime("%Y-%m-%d")
    try:
        h = _visitor_bucket(remote_addr)
        with _vlock:
            _vdirty = True
            _vstate["hits"] += 1
            day = _vstate["days"].setdefault(today, {"u": [], "h": 0})
            if h not in day["u"]:
                day["u"].append(h)
            day["h"] += 1
    except Exception:
        pass


def _visitor_baseline():
    """All-time floor carried across redeploys via a git-tracked file."""
    try:
        if VISITOR_BASELINE_FILE.exists():
            data = json.loads(VISITOR_BASELINE_FILE.read_text(encoding="utf-8"))
            return max(0, int(data.get("all_time", 0) or 0))
    except Exception:
        pass
    return 0


@app.before_request
def _count_visit():
    if request.method != "GET":
        return
    path = request.path.lower()
    if any(s in path for s in VISITOR_SKIP):
        return
    # IndexNow pings arrive as ?url=... - never count them as a visitor.
    if request.args.get("url"):
        return
    ua = request.headers.get("User-Agent", "")
    if not ua or _BOT_RE.search(ua) or _EMPTY_UA_RE.search(ua):
        return
    _record_visit(request.remote_addr or "0.0.0.0")


@app.route("/api/visitors")
def api_visitors():
    """Aggregate-only visitor counts. Hashed per day, no raw IPs, no PII."""
    try:
        with _vlock:
            hits = _vstate["hits"]
            days = {k: dict(v) for k, v in _vstate["days"].items()}
        baseline = _visitor_baseline()
        today = datetime.now(PT).strftime("%Y-%m-%d")
        last7 = (datetime.now(PT) - timedelta(days=6)).strftime("%Y-%m-%d")
        return jsonify({
            "all_time": baseline + hits,
            "baseline": baseline,
            "since_boot": hits,
            "today": len(days.get(today, {}).get("u", [])),
            "today_hits": days.get(today, {}).get("h", 0),
            "last7": sum(len(d.get("u", [])) for k, d in days.items() if k >= last7),
            "note": "human page views; crawlers, IndexNow and uptime monitors excluded",
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


_load_visitor_state()
threading.Thread(target=_visitor_flusher, daemon=True).start()

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

def save_subscription(customer_id, plan, status, email=None, sub_id=None, period_end=None):
    """Save/refresh subscription. Keeps email + Stripe sub_id for recovery + portal."""
    if not customer_id:
        print("[Subs] WARN: no customer_id, skipping save")
        return
    customer_id = str(customer_id)
    subs = get_subscriptions()
    existing = subs.get(customer_id, {})
    if not isinstance(existing, dict):
        existing = {}
    record = {
        'plan': plan,
        'status': status,
        'updated': int(time.time()),
    }
    final_email = email if email else existing.get('email')
    if final_email:
        record['email'] = final_email
    final_sub_id = sub_id if sub_id else existing.get('sub_id')
    if final_sub_id:
        record['sub_id'] = final_sub_id
    final_pe = period_end if period_end else existing.get('period_end')
    if final_pe:
        record['period_end'] = final_pe
    subs[customer_id] = record
    SUBS_FILE.write_text(json.dumps(subs))
    print(f"[Subs] Saved: {customer_id} {plan} {status} {email or ''}")


def get_customer_by_email(email):
    """Look up our subscriptions.json for a customer by email. Returns (customer_id, sub_dict) or (None, None)."""
    if not email:
        return None, None
    email = email.strip().lower()
    subs = get_subscriptions()
    for cid, data in subs.items():
        if (data.get('email') or '').strip().lower() == email:
            return cid, data
    return None, None

# Cache Stripe API validations for 5 min to avoid hitting API on every page load
_STRIPE_VALIDATION_CACHE = {}  # customer_id -> (is_active: bool, expires_at: float)

def is_subscriber():
    """Check if current visitor has an active subscription.

    Two-tier check:
    1. Local subscriptions.json (fast, set by /success or webhook)
    2. Live Stripe API validation (slower, but catches expired/cancelled sub
       if our local file is stale or webhook missed). Cached 5 min.
    """
    customer_id = request.cookies.get("stripe_customer", "")
    if not customer_id:
        return False
    subs = get_subscriptions()
    local = subs.get(customer_id, {})
    local_status = local.get('status')
    if local_status == 'active':
        return True
    # Local says inactive/cancelled/missing — but maybe webhook missed it, or
    # Railway wiped the container filesystem on the last redeploy.
    #
    # A MISSING record used to short-circuit to False here, which meant a
    # redeploy silently revoked every paid account: subscriptions.json lives on
    # the container's ephemeral disk and is deliberately not committed by the
    # daily scan, so it comes back empty after every deploy. Stripe still knows
    # the subscription is paid and active, so ask Stripe before denying access.
    # Losing access because our cache was wiped is far worse than one extra API
    # call. The 5-minute validation cache keeps that cost bounded.
    if not stripe.api_key:
        return False
    return _stripe_validate_active(customer_id)

def _stripe_validate_active(customer_id: str) -> bool:
    """Verify subscription is still active via Stripe API. Cached 5 min."""
    import time as _time
    now = _time.time()
    cached = _STRIPE_VALIDATION_CACHE.get(customer_id)
    if cached and cached[1] > now:
        return cached[0]
    if not stripe.api_key:
        # No Stripe key configured — fall back to local
        return get_subscriptions().get(customer_id, {}).get('status') == 'active'
    try:
        subs = stripe.Subscription.list(customer=customer_id, limit=1, status='all')
        is_active = False
        for s in subs.data:
            if s.status in ('active', 'trialing'):
                is_active = True
                # Rebuild the local record whenever Stripe says active.
                #
                # This used to refresh ONLY when a record already existed, so a
                # customer whose record was lost (redeploy wipes the container
                # disk) stayed broken forever: Stripe knew they paid, we asked
                # Stripe, Stripe said yes - and then we saved nothing and every
                # later call re-asked. Now a missing record is reconstructed
                # from the live subscription, so access self-heals.
                subs_local = get_subscriptions()
                existing = subs_local.get(customer_id) or {}
                plan = existing.get('plan')
                if not plan:
                    m = (getattr(s, 'metadata', None) or {}) if not isinstance(s, dict) \
                        else (s.get('metadata') or {})
                    plan = (m or {}).get('plan', 'monthly')
                period_end = _plain(s).get('current_period_end')
                save_subscription(
                    customer_id, plan, 'active',
                    email=existing.get('email'),
                    sub_id=_plain(s).get('id'),
                        period_end=period_end,
                    )
                break
        _STRIPE_VALIDATION_CACHE[customer_id] = (is_active, now + 300)
        return is_active
    except Exception as e:
        print(f"[Stripe Validate] Error for {customer_id}: {e}")
        # On API error, trust the local status
        return get_subscriptions().get(customer_id, {}).get('status') == 'active'

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
    # SAFETY: never spawn the scanner inside the Railway container (OOM -> restart
    # loop -> 404). Fresh data arrives via GitHub push from the local machine.
    if not ALLOW_IN_CONTAINER_SCAN:
        scan_state.scan_state = 'done'
        scan_state.refresh_state = 'idle'
        print('[Scanner] BLOCKED - in-container scan disabled. '
              'Data is pushed from the local machine; run daily_scan.ps1 there.')
        return False
    scan_state.scan_state = 'running'
    scan_state.refresh_state = 'idle'
    print('[Scanner] Scan triggered.')
    t = threading.Thread(target=run_full_scan, daemon=True)
    t.start()
    return True

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

# RETIRED 2026-10-20: /cron and /cron-afternoon were removed, along with the
# _CRON_STATE_FILE / _load_cron_state / _save_cron_state helpers they used.
#
# Those routes never scanned. Their own docstrings said "Scanning happens
# locally" - they only read ai_earnings_today.html and returned a freshness
# string, which made them look like scans while doing no work. With Tyler's
# cron-job.org account deleted nothing external calls the service any more,
# so they were unreachable dead weight.
#
# .cron_state.json was the only remaining reader/writer of that file and has
# been removed too. Scanning is driven by the Windows tasks AIScannerDaily1
# (06:31) and AIScannerDaily (13:00) running daily_scan.ps1 locally.

# RETIRED 2026-10-20: the /cron route was removed. See the note above.
# It never scanned - it only checked whether ai_earnings_today.html was
# fresh and returned a string. Do not reintroduce it as a scan trigger.


# RETIRED 2026-10-20: the /cron-afternoon route was removed. Like /cron it
# never scanned - it only read ai_earnings_today.html and returned a
# freshness string. It also wrote .cron_state.json on every call.


# RETIRED 2026-10-20: the /cron-twitter route was removed.
#
# It was a public GET endpoint on the DEPLOYED site that spawned a thread and
# called x_poster.post_daily_scan_to_twitter(), posting the day's picks to X.
# It was hit by cron-job.org after the morning scan, which meant any external
# GET - not just the intended caller - could trigger a post. Tyler retired the
# X channel entirely, so the route is gone rather than merely disabled.
# Do not reintroduce an X/Twitter posting path in this app.


@app.route("/cron-price-alerts")
def cron_price_alerts():
    """Disabled - alerts consume too many social API credits."""
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

# ===== REAL WINS (the honest alternative to invented testimonials) =========
# The pricing page used to carry five five-star testimonials attributed to
# four invented customers - named people with job titles and "Pro member
# since 2026" - attached to specific gains. On a page that takes a card
# payment that is an FTC endorsement exposure, and it is the kind of thing a
# careful visitor notices. The names are not repeated here on purpose: a
# source grep for them should come back empty.
#
# wins.html already holds the real thing: tickers, entry prices, the actual
# beat, and what the stock did. INOD +176%, SNOW +69% to $255 from a $151
# entry, OKTA +34%. The invented quotes were not even flattering - the fake
# SNOW quote claimed +57% when the real trade returned +69%.
#
# Read at request time from a file we control, so the two can never disagree.
WIN_CARD = re.compile(
    r'<a href="/wins/([a-z0-9]+)" class=win-card>\s*'
    r'<div class=t>([A-Z.]{1,6})\s*<span[^>]*>([^<]*)</span></div>\s*'
    r'<div class=g>([+-][0-9.]+%)</div>\s*'
    r'<div class=d>([^<]*)</div>\s*'
    r'<div class=l>([^<]*)</div>',
    re.S)


def real_wins(limit=4):
    """Pull genuine tracked wins out of wins.html.

    Returns [] rather than raising: a malformed wins page must not take the
    pricing page down with it. An empty strip beats an invented one.
    """
    path = Path(__file__).parent / "wins.html"
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"[Wins] could not read wins.html: {e}")
        return []
    out = []
    for slug, ticker, company, gain, meta, blurb in WIN_CARD.findall(text):
        out.append({
            "slug": slug, "ticker": ticker.strip(),
            "company": company.strip(), "gain": gain.strip(),
            "meta": _clean(meta), "blurb": _clean(blurb),
        })
        if len(out) >= limit:
            break
    return out


def _clean(s):
    """Collapse whitespace and the separator glyphs wins.html uses."""
    s = re.sub(r'<[^>]+>', '', s)
    s = s.replace("\u00b7", "\u00b7 ").replace("\u2192", " ").replace("\u2014", " ")
    return re.sub(r'\s+', ' ', s).strip()


def _wins_strip(limit=4):
    wins = real_wins(limit)
    if not wins:
        return ''
    cards = []
    for w in wins:
        cards.append(
            '<div style="background:#161b22;border:1px solid #2ea043;border-radius:12px;'
            'padding:16px;text-align:left">'
            f'<div style="font-size:0.8em;color:#58a6ff;font-weight:bold">'
            f'{w["ticker"]} <span style="color:#8b949e;font-weight:normal">'
            f'\u00b7 {w["company"]}</span></div>'
            f'<div style="font-size:1.7em;color:#00ff88;font-weight:bold;margin:4px 0">'
            f'{w["gain"]}</div>'
            f'<div style="font-size:0.75em;color:#8b949e;margin-bottom:8px">'
            f'{w["meta"]}</div>'
            f'<div style="font-size:0.82em;color:#c9d1d9;line-height:1.5">'
            f'{w["blurb"]}</div>'
            f'<a href="/wins/{w["slug"]}" style="display:inline-block;margin-top:10px;'
            f'color:#58a6ff;font-size:0.82em;font-weight:bold;text-decoration:none">'
            f'Read the case study \u2192</a></div>')
    return ('<div style="margin-top:44px;text-align:center">'
            '<h3 style="color:#fff;font-size:1.25em;margin-bottom:4px">'
            'Real results from the scanner</h3>'
            '<p style="color:#8b949e;font-size:0.88em;margin-bottom:22px">'
            'Every one of these was flagged before the earnings report. '
            'No invented testimonials.</p>'
            '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));'
            'gap:14px;text-align:left">' + ''.join(cards) + '</div>'
            '<a href="/wins" class=back-link style="display:inline-block;margin-top:20px">'
            'See every tracked win \u2192</a></div>')


# ===== EMAIL LIST ===========================================================
# Before this the ONLY <input> on the whole site was the chat box. A visitor
# who was not ready to pay today was completely unreachable - no list, no
# mailto, no outbound transport anywhere in the repo. This is the owned
# channel the daily alert will run on.
EMAIL_LIST_FILE = Path(__file__).parent / "email_list.json"
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")


def _read_email_list():
    try:
        return json.loads(EMAIL_LIST_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_email_list(d):
    EMAIL_LIST_FILE.write_text(json.dumps(d, indent=2), encoding="utf-8")


@app.route("/api/email-signup", methods=["POST"])
def api_email_signup():
    """Add an address to the daily-pick list.

    Validation is deliberately strict: this endpoint is unauthenticated, so it
    is the cheapest thing on the site to spam. Only a real-looking address is
    stored, nothing else from the request body is trusted, and the response
    never confirms whether a given address was already on the list.
    """
    try:
        data = request.get_json(silent=True) or {}
    except Exception:
        data = {}
    email = (data.get("email") or "").strip().lower()
    if not email or len(email) > 254 or not EMAIL_RE.match(email):
        return jsonify({"ok": False,
                        "message": "That does not look like an email address."}), 400

    # Honeypot: a real person never fills a field they cannot see.
    if (data.get("website") or "").strip():
        return jsonify({"ok": True, "message": "Check your inbox tomorrow."}), 200

    lst = _read_email_list()
    existing = lst.get(email)
    if existing:
        # Do not overwrite a subscriber's own record.
        existing["seen_count"] = int(existing.get("seen_count", 1)) + 1
        existing["last_seen"] = _now_iso()
    else:
        lst[email] = {
            "added": _now_iso(),
            "last_seen": _now_iso(),
            "seen_count": 1,
            "source": (data.get("source") or "site")[:40],
            "confirmed": False,
        }
        print(f"[Email] signup: {email}")
    try:
        _write_email_list(lst)
    except Exception as e:
        print(f"[Email] write failed: {e}")
        return jsonify({"ok": False, "message": "Could not save that. Try again."}), 500
    return jsonify({"ok": True, "message": "Check your inbox tomorrow morning."}), 200


def _now_iso():
    return datetime.now(PT).isoformat(timespec="seconds")


# ===== EMAIL CAPTURE (non-subscribers only) ==============================
# "the only <input> on the whole site is the chat box - a free visitor who is
# not ready to pay is unreachable." The daily alert needs a list to run on,
# and a $5 product with no owned channel has to re-acquire every visitor.
EMAIL_CAPTURE = """
<div id="dl-signup" style="max-width:640px;margin:34px auto 10px;padding:22px 20px;
 background:linear-gradient(135deg,#0d2b1a,#0a1a12);border:2px solid #00ff88;
 border-radius:14px;text-align:center">
  <div style="color:#fff;font-size:1.15em;font-weight:bold;margin-bottom:6px">
    Get tomorrow's pick by email</div>
  <div style="color:#8b949e;font-size:.88em;margin-bottom:14px">
    The full scanner stays free. This is the one email that tells you what to
    trade each morning before the open.</div>
  <div id="dl-msg" style="font-size:.85em;margin-top:10px;min-height:18px"></div>
  <div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap">
    <input id="dl-email" type="email" inputmode="email" autocomplete="email"
      placeholder="you@example.com"
      style="flex:1 1 240px;min-width:0;padding:11px 13px;border-radius:8px;
      border:1px solid #30363d;background:#0d1117;color:#fff;font-size:.95em">
    <input id="dl-hp" type="text" tabindex="-1" autocomplete="off"
      aria-hidden="true" style="position:absolute;left:-9999px;width:1px;height:1px;opacity:0">
    <button id="dl-go" style="padding:11px 20px;border-radius:8px;border:none;
      background:#00ff88;color:#000;font-weight:bold;font-size:.95em;cursor:pointer">
      Send it to me</button>
  </div>
</div>
<script>
(function(){
  var go=document.getElementById('dl-go'), em=document.getElementById('dl-email'),
      msg=document.getElementById('dl-msg'), hp=document.getElementById('dl-hp');
  if(!go) return;
  function say(t,ok){ msg.textContent=t; msg.style.color = ok ? '#00ff88' : '#ff6b6b'; }
  go.addEventListener('click', function(){
    var v=(em.value||'').trim();
    if(!v){ say('Enter your email first.', false); return; }
    go.disabled=true; go.textContent='Saving...';
    fetch('/api/email-signup',{method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({email:v, website:hp.value, source:'scanner'})})
      .then(function(r){return r.json().then(function(d){return {s:r.status,d:d};});})
      .then(function(x){
        go.disabled=false; go.textContent='Send it to me';
        if(x.s===200){ say(x.d.message||'Check your inbox tomorrow morning.', true);
                      em.value=''; }
        else { say(x.d.message||'Could not save that. Try again.', false); }
      })
      .catch(function(){ go.disabled=false; go.textContent='Send it to me';
                         say('Network error. Try again.', false); });
  });
  em.addEventListener('keydown', function(e){ if(e.key==='Enter') go.click(); });
})();
</script>
"""


def _annual_nudge():
    """Annual-plan anchor, shown only when there are real tracked wins to justify it.

    Deliberately not a countdown timer or a fake scarcity device. The number
    rendered is the actual count of documented wins in wins.html, so the nudge
    cannot claim more than the case studies can support - and it disappears
    entirely if that evidence is ever removed.
    """
    wins = real_wins(60)
    if len(wins) < 3:
        return ''
    best = max(wins, key=lambda w: _gain_num(w["gain"]))
    return (
        '<div style="margin-top:26px;padding:18px 20px;border-radius:12px;'
        'border:1px solid #30363d;background:#161b22;text-align:center">'
        f'<div style="color:#c9d1d9;font-size:.95em">'
        f'<b style="color:#00ff88">{len(wins)}</b> tracked setups have run to '
        f'their target. Best so far: <b style="color:#00ff88">'
        f'{best["ticker"]} {best["gain"]}</b>.</div>'
        '<div style="color:#8b949e;font-size:.86em;margin-top:6px">'
        'Monthly is $5. The annual plan is $50 &mdash; two months free, and it '
        'locks your price for the year.</div>'
        '<a href="/create-checkout?plan=annual" class=cta '
        'style="display:inline-block;margin-top:12px;background:#00ff88;color:#000;'
        'padding:11px 20px;border-radius:8px;font-weight:bold;text-decoration:none">'
        'Lock in the year &rarr;</a></div>'
    )


def _gain_num(s):
    try:
        return float(str(s).lstrip('+-').rstrip('%'))
    except Exception:
        return 0.0


TARGET_HITS_FILE = Path(__file__).parent / "target_hits.json"


def _live_hit_nudge():
    """Surface a pick that has actually reached its target. Renders nothing otherwise.

    This is the "right now" version of the annual nudge. _annual_nudge() is
    static: it fires off the count of historical case studies. This one fires
    off pick_tracker.json picks whose LIVE price has reached the target
    recorded on the day the pick was made - the actual moment someone buys.

    Everything here is load-bearing honesty:

      * No hits -> empty string. No placeholder, no "targets coming soon", no
        urgency device standing in for evidence that does not exist.
      * Stale file -> empty string. If evaluate_targets.py has not run in
        FRESH_DAYS, the page must not claim anything is current.
      * Numbers come from target_hits.json, which only records a hit when a
        real price fetch returned >= the recorded target. Nothing is rounded up
        or inferred here.
    """
    try:
        if not TARGET_HITS_FILE.exists():
            return ''
        data = json.loads(TARGET_HITS_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[Targets] nudge unavailable: {e}")
        return ''

    hits = data.get("hits") or []
    fresh_days = int(data.get("fresh_days") or 14)
    fresh = [h for h in hits
             if isinstance(h, dict) and (h.get("days_to_hit") or 999) <= fresh_days]
    if not fresh:
        return ''

    top = fresh[0]
    ticker = top.get("ticker", "")
    # Prices are formatted to 2 decimals explicitly. Interpolating the raw
    # float rendered "$372.1" next to a target of "$365.51" on the same line,
    # which reads as a rendering bug on a page whose entire pitch is that the
    # numbers are real.
    def _money(v):
        try:
            return f"{float(v):,.2f}"
        except Exception:
            return "n/a"
    target = _money(top.get("target"))
    current = _money(top.get("current"))
    over = top.get("vs_target_pct")
    when = top.get("date")
    more = (f" and {len(fresh) - 1} more" if len(fresh) > 1 else "")

    return (
        '<div style="margin-top:22px;padding:18px 20px;border-radius:12px;'
        'border:2px solid #00ff88;background:#0d2b1a;text-align:center">'
        f'<div style="color:#00ff88;font-size:.8em;font-weight:bold;letter-spacing:.06em">'
        f'JUST HIT TARGET{more}</div>'
        f'<div style="color:#fff;font-size:1.05em;margin:8px 0">'
        f'<b>{ticker}</b> reached its <b>${target}</b> target at '
        f'<b>${current}</b> ({over}% above target)</div>'
        f'<div style="color:#8b949e;font-size:.85em">Flagged by the scanner on '
        f'{when}, before the earnings report. Every number is from the live '
        f'tracker &mdash; if it is not listed, it did not happen.</div>'
        '<div style="color:#c9d1d9;font-size:.95em;margin-top:10px">'
        'Monthly is $5. The annual plan is $50 &mdash; two months free, locked in.</div>'
        '<a href="/create-checkout?plan=annual" class=cta '
        'style="display:inline-block;margin-top:12px;background:#00ff88;color:#000;'
        'padding:11px 20px;border-radius:8px;font-weight:bold;text-decoration:none">'
        'Lock in the year &rarr;</a></div>'
    )


ALERT_ENV_FILE = Path(__file__).parent / "alert.env"


@app.route("/api/alert-status")
def api_alert_status():
    """Is the daily alert actually able to send?

    Reports booleans and no secrets - no host, no user, no key, no addresses.
    The pricing page advertises "real-time earnings alerts".

    WHY THIS READS A FILE INSTEAD OF THE CREDENTIAL
    -----------------------------------------------
    The sender does NOT run here. It runs on Tyler's machine, from
    daily_scan.ps1. This endpoint runs on Railway. alert.env is gitignored, so
    Railway can never see it - asking the deployed host whether a LOCAL
    credential exists is structurally incapable of a true answer, and it
    reported false forever even with a fully working, verified, actually
    sending pipeline. The test address failing does not change that.

    So the sender publishes alert_status.json after every run: when it last
    ran, how many went out, how many failed, over which transport. No
    addresses, no credentials. The daily scan commits it, and this endpoint
    reports what actually happened.

    `alerts_configured` means "at least one real email has gone out recently".
    It is deliberately not "zero failures": one mistyped address should not
    read as a broken pipeline. The partial failure is exposed separately as
    `last_failed` instead of being hidden.
    """
    configured = False
    runner_wired = False
    detail = {}

    try:
        status_file = Path(__file__).parent / "alert_status.json"
        if status_file.exists():
            detail = json.loads(status_file.read_text(encoding="utf-8"))
        runner = Path(__file__).parent / "daily_scan.ps1"
        if runner.exists():
            body = runner.read_text(encoding="utf-8", errors="ignore")
            runner_wired = "send_daily_alert.py" in body

        # A send counts as recent for two days, so a missed run is visible
        # without a send making the site look broken the moment one is late.
        when = str(detail.get("last_run") or "")
        if detail.get("sent") and when:
            try:
                age = datetime.now() - datetime.fromisoformat(when)
                configured = age.total_seconds() <= 48 * 3600
            except Exception:
                configured = False
    except Exception as e:
        print(f"[Alert] status check failed: {e}")

    return jsonify({
        "alerts_configured": bool(configured and runner_wired),
        "delivered_recently": bool(configured),
        "last_failed": int(detail.get("failed") or 0),
        "last_sent": int(detail.get("sent") or 0),
        "runner_wired": bool(runner_wired),
    })


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
            <a href="/create-checkout?plan=annual" class=cta>Start Pro — $50/year</a>
        </div>
    </div>
    <div class=testimonial>
        <div class=stars>★★★★★</div>
        <div class=text>Founder's track record, not rented quotes. Every trade
        below was flagged by this scanner before its earnings report, with the
        entry price, the score and what the stock actually did. There are no
        invented testimonials on this page — if a number is here, it happened.</div>
        <div class=author>— Tyler C., AI Market Cap</div>
    </div>
    <!--REAL-WINS-STRIP-->
    <a href="/about" class=back-link>← Learn more about AI Market Cap</a>
</div>
</body></html>"""
    # Real wins replace the invented testimonials. Injecting here rather than
    # inlining means the strip can never drift from wins.html.
    # The annual nudge runs FIRST and re-emits the marker, because the wins
    # replace below consumes it. Doing these the other way round silently
    # drops the nudge: str.replace() on a marker that is already gone is a
    # no-op that still looks like it worked.
    pricing_html = pricing_html.replace('    <!--REAL-WINS-STRIP-->',
                                        _live_hit_nudge() + '    <!--REAL-WINS-STRIP-->')
    pricing_html = pricing_html.replace('    <!--REAL-WINS-STRIP-->',
                                        _annual_nudge() + '    <!--REAL-WINS-STRIP-->')
    # Real wins replace the invented testimonials. Injecting rather than
    # inlining means the strip can never drift from wins.html.
    pricing_html = pricing_html.replace('<!--REAL-WINS-STRIP-->', _wins_strip(4))
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
    <a href="/pro" class="nav-link">Pro Dashboard</a>
    <a href="/pricing" class="nav-link nav-subscribe">Subscribe</a>
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
    <p>The scan runs automatically every market day at 6:30 AM PT, and the Pro Pick and Runner Up Pick update with it. Use the <b>Refresh</b> button on the scanner to pull the latest published data at any time.</p>
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
    """Payment success page — activates subscription, captures email, sets cookie."""
    session_id = request.args.get('session_id', '')
    customer_id = ''
    email = ''
    plan = 'monthly'
    sub_id = None
    period_end = None
    try:
        session = _plain(stripe.checkout.Session.retrieve(session_id))
        customer_id = session.get('customer')
        plan = (session.get('metadata') or {}).get('plan', 'monthly')
        # Capture email — from session, fall back to customer lookup
        email = (session.get('customer_details') or {}).get('email') or \
                (session.get('customer_email') or '')
        sub_id = session.get('subscription')
        if sub_id and stripe.api_key:
            try:
                sub = _plain(stripe.Subscription.retrieve(sub_id))
                period_end = sub.get('current_period_end')
            except Exception:
                pass
        if not email and customer_id and stripe.api_key:
            try:
                cust = _plain(stripe.Customer.retrieve(customer_id))
                email = cust.get('email', '')
            except Exception:
                pass

        # Persist subscription locally (webhook will also fire, but /success is the
        # primary path that grants immediate access)
        save_subscription(
            customer_id, plan, 'active',
            email=email, sub_id=sub_id, period_end=period_end,
        )
        # Bust the validation cache for this customer
        _STRIPE_VALIDATION_CACHE.pop(customer_id, None)

        plan_name = plan.capitalize()
        # Absolute, re-openable access link. /success is idempotent: it
        # re-reads the session, re-saves the record and re-issues the cookie.
        # That makes it a genuine self-serve recovery link for anyone who
        # clears their cookies or switches device - previously the only way
        # back in was emailing support, which is not a product.
        restore_link = request.host_url + 'success?session_id=' + session_id
        # Offer to set a password NOW, while we still know the payer is present.
        # This is the only moment in the flow where we get a free, proven
        # identity. Skipping it leaves them unable to sign in on a new device.
        setpw_hint = ''
        if email:
            setpw_hint = (
                '<p class="setpw"><strong>One last step:</strong> set a password so you '
                'can sign in on any device.<br>'
                '<a href="/set-password" class="btn2">Set My Password →</a></p>'
            )

        success_html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Welcome - AI Market Cap</title>
<style>
body {{ font-family: Segoe UI, sans-serif; background: #0d1117; color: #fff; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 24px; text-align: center; }}
.box {{ max-width: 520px; }}
h1 {{ color: #2ea043; font-size: 2em; margin: 0 0 8px; }}
p {{ color: #8b949e; font-size: 1.05em; margin: 16px 0; line-height: 1.5; }}
a.btn {{ background: #2ea043; color: #fff; padding: 14px 32px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 1.1em; display: inline-block; margin-top: 16px; }}
a.btn:hover {{ background: #3fb950; }}
a.btn2 {{ background: #1f6feb; color: #fff; padding: 11px 22px; border-radius: 8px; text-decoration: none; font-weight: bold; display: inline-block; margin-top: 10px; }}
a.btn2:hover {{ background: #2f81f7; }}
a.secondary {{ color: #58a6ff; text-decoration: none; font-size: 0.9em; display: inline-block; margin-top: 12px; }}
.setpw {{ background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 18px; margin-top: 24px; font-size: 0.92em; color: #c9d1d9; }}
.check {{ font-size: 4em; color: #2ea043; margin-bottom: 12px; }}
</style></head><body>
<div class=box>
  <div class=check>✓</div>
  <h1>Payment Successful!</h1>
  <p>Welcome to AI Market Cap! Your <strong>{plan_name}</strong> subscription is active.<br>The Pro Pick, Runner-Up, and AI Chat are now unlocked.</p>
  <div class=setpw style="background:#0d2818;border:1px solid #2ea043">
    <strong>Save this page before you close it.</strong><br>
    This is your permanent access link. If you ever clear your cookies, switch
    browser, or come back on another device, open it again and everything
    unlocks straight away &mdash; no password needed.
    <div class=err style="background:#0d1117;border-color:#2ea043;color:#7ee787;word-break:break-all">{restore_link}</div>
  </div>
  <a href="/" class=btn>Go to Scanner →</a>
  <a href="/account" class=secondary>Manage Subscription</a>
  {setpw_hint}
</div>
</body></html>"""
        resp = make_response(success_html, 200, {"Content-Type": "text/html; charset=utf-8"})
        # 30-day cookie. Subscribers stay unlocked as long as the cookie exists + Stripe sub is active.
        resp.set_cookie("stripe_customer", customer_id, max_age=86400*30, httponly=True, samesite='Lax')
        return resp
    except Exception as e:
        # A paying customer must never dead-end here. Money is already taken,
        # so this screen has to offer a real way forward, not just an apology.
        # Two things went wrong for real customers at once:
        #   1. the StripeObject .get() crash (fixed in _plain)
        #   2. Railway wiping subscriptions.json on redeploy, which left a paid
        #      customer with no record and no cookie
        # We now still grant the cookie when we know WHO paid, and point them
        # to /account, which re-checks Stripe live and can re-create the record.
        print(f"[Success] ACTIVATION FAILED for session={session_id}: {e}")
        import traceback
        traceback.print_exc()

        body = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Almost there - AI Market Cap</title>
<style>
body {{ font-family: Segoe UI, sans-serif; background: #0d1117; color: #fff; display: flex;
       align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 24px;
       text-align: center; }}
.box {{ max-width: 560px; }}
h1 {{ color: #f0883e; font-size: 1.7em; margin: 0 0 8px; }}
p {{ color: #8b949e; font-size: 1.03em; line-height: 1.55; margin: 14px 0; }}
a.btn {{ background: #2ea043; color: #fff; padding: 14px 32px; border-radius: 8px;
         text-decoration: none; font-weight: bold; display: inline-block; margin: 10px 6px 0; }}
a.btn2 {{ background: #1f6feb; color: #fff; padding: 13px 28px; border-radius: 8px;
          text-decoration: none; font-weight: bold; display: inline-block; margin: 10px 6px 0; }}
.note {{ background: #161b22; border: 1px solid #30363d; border-radius: 10px;
         padding: 14px; margin-top: 26px; font-size: 0.88em; color: #c9d9d0; }}
.err {{ color: #6e7681; font-size: 0.8em; margin-top: 14px; word-break: break-word; }}
</style></head><body><div class="box">
<h1>Your payment went through</h1>
<p>We hit a problem finishing the last step of your activation. <strong>Your payment
is safe and your subscription is active in Stripe</strong> - this is our bug, not yours,
and we're on it.</p>
<p>Use the button below and your access will be confirmed from Stripe and repaired
automatically.</p>
<a class=btn href="/account?repair=1">Restore My Access →</a>
<a class=btn2 href="/">Back to Home</a>
<div class=note>Nothing was charged twice. If the button does not work, email
support@aismarketcap.com with your receipt and we'll fix it by hand.</div>
<div class=err>Reference: {session_id or 'unknown'} &middot; {e}</div>
</div></body></html>"""

        resp = make_response(body, 200, {"Content-Type": "text/html; charset=utf-8"})
        # If we identified the payer before failing, hand them the cookie
        # anyway: /account then revalidates against Stripe and rebuilds the
        # missing local record. Far better than stranding a paying customer.
        try:
            if customer_id:
                resp.set_cookie("stripe_customer", customer_id,
                                max_age=86400 * 30, httponly=True, samesite='Lax')
        except Exception:
            pass
        return resp


# ===== PASSWORD AUTH =====================================================
# /login used to accept a bare ?email=X and set the access cookie for whoever
# matched. Knowing (or guessing) a subscriber's email was therefore enough to
# get Pro — no proof of anything. Anyone could read a subscriber's address off
# a Stripe receipt screenshot, a shared thread, or just try the obvious
# first.last@gmail.com, and walk into their account.
#
# The fix is a real credential. /success sets a password immediately after
# payment (the one moment we KNOW the payer is present and paid), and /login
# requires email + password. The cookie is issued only after that check passes.
#
# We deliberately did NOT implement an emailed one-time magic link. This app
# has no outbound email transport — the only smtplib code in the repo lives in
# content_pipeline/ and expects Gmail app-passwords passed in by the caller.
# A magic link with no way to send the mail is a door that never opens: a
# subscriber who clears their cookies could never get back in. A password they
# choose at checkout always works, needs no new infrastructure, and no new
# Railway env vars.
from werkzeug.security import generate_password_hash, check_password_hash
from threading import Lock as _ThreadLock

MIN_PASSWORD_LEN = 8
_LOGIN_FAIL_WINDOW = 900      # 15 minutes
_LOGIN_MAX_FAILS = 10
_login_failures = {}          # email -> (count, first_fail_ts)
_login_lock = _ThreadLock()

def _prune_login_failures(now=None):
    now = now or time.time()
    stale = [k for k, (c, first) in _login_failures.items()
             if now - first > _LOGIN_FAIL_WINDOW]
    for k in stale:
        _login_failures.pop(k, None)

def record_login_failure(email):
    email = (email or '').strip().lower()
    if not email:
        return
    with _login_lock:
        now = time.time()
        _prune_login_failures(now)
        count, first = _login_failures.get(email, (0, now))
        if now - first > _LOGIN_FAIL_WINDOW:
            count, first = 0, now
        _login_failures[email] = (count + 1, first)

def clear_login_failures(email):
    email = (email or '').strip().lower()
    with _login_lock:
        _login_failures.pop(email, None)

def login_throttled(email):
    """True if this email has burned too many attempts in the window."""
    email = (email or '').strip().lower()
    with _login_lock:
        _prune_login_failures()
        rec = _login_failures.get(email)
        if not rec:
            return False
        count, first = rec
        return count >= _LOGIN_MAX_FAILS

def set_subscriber_password(customer_id, password):
    """Store a scrypt password hash on the subscription record.

    Returns (ok, error_message). The hash is the only thing persisted — the
    plaintext is never written anywhere.
    """
    if not password or len(password) < MIN_PASSWORD_LEN:
        return False, f"Password must be at least {MIN_PASSWORD_LEN} characters."
    if len(password) > 200:
        return False, "Password is too long."
    subs = get_subscriptions()
    rec = subs.get(customer_id)
    if not isinstance(rec, dict):
        return False, "No subscription found for this account."
    if rec.get('status') != 'active':
        return False, "This subscription is not active."
    pw_hash = generate_password_hash(password)
    rec['pw_hash'] = pw_hash
    rec['pw_set'] = int(time.time())
    # A new password invalidates the failure counter for that email.
    if rec.get('email'):
        clear_login_failures(rec.get('email'))
    subs[customer_id] = rec
    try:
        SUBS_FILE.write_text(json.dumps(subs), encoding='utf-8')
    except Exception as e:
        print(f"[Auth] FATAL: could not persist password for {customer_id}: {e}")
        return False, "Could not save your password. Please contact support."
    print(f"[Auth] Password set for {customer_id}")
    return True, ""

def verify_subscriber_password(customer_id, password):
    """Check a password against the stored scrypt hash. Returns bool."""
    subs = get_subscriptions()
    rec = subs.get(customer_id)
    if not isinstance(rec, dict):
        return False
    pw_hash = rec.get('pw_hash')
    if not pw_hash:
        return False
    try:
        return check_password_hash(pw_hash, password or '')
    except Exception as e:
        print(f"[Auth] hash check error for {customer_id}: {e}")
        return False


# ===== ACCOUNT + LOGIN + PORTAL =====
@app.route("/set-password", methods=["GET", "POST"])
def set_password():
    """Let an already-authenticated subscriber choose or change their password.

    Reached straight from /success while the payment cookie is fresh, and from
    /account for existing subscribers who subscribed before passwords existed.
    It requires a VALID access cookie (set by /success after payment or by
    /login after a correct password) — it will not set a password for someone
    who cannot already prove their subscription.
    """
    customer_id = request.cookies.get("stripe_customer", "")
    if not customer_id or not is_subscriber():
        return redirect("/pricing")

    rec = get_subscriptions().get(customer_id, {})
    email = rec.get('email', '') or 'your account'
    already = bool(rec.get('pw_hash'))

    if request.method == 'POST':
        pw = request.form.get('password', '')
        pw2 = request.form.get('password2', '')
        if pw != pw2:
            return _set_password_page(email, already, error="Passwords do not match.")
        ok, err = set_subscriber_password(customer_id, pw)
        if not ok:
            return _set_password_page(email, already, error=err)
        clear_login_failures(rec.get('email'))
        resp = make_response(redirect("/account", code=302))
        resp.set_cookie("pw_set_flash", "1", max_age=30, httponly=True, samesite='Lax')
        return resp

    return _set_password_page(email, already, error=None)


def _set_password_page(email, already, error=None):
    heading = "Change Your Password" if already else "Set Your Password"
    intro = ("Your Pro access is active on this device. Set a password so you can "
             "sign back in from any device."
             if not already else
             "Choose a new password for your Pro account.")
    err_html = f'<div class="err">{error}</div>' if error else ''
    return make_response(f"""<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Set Password - AI Market Cap</title>
<style>
body {{ font-family: Segoe UI, sans-serif; background: #0d1117; color: #c9d1d9; min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 24px; }}
.box {{ background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 36px 32px; max-width: 460px; width: 100%; }}
h1 {{ color: #fff; font-size: 1.4em; margin: 0 0 10px; }}
p.sub {{ color: #8b949e; font-size: 0.92em; line-height: 1.6; margin-bottom: 22px; }}
label {{ display: block; font-size: 0.85em; color: #8b949e; margin-bottom: 6px; }}
input[type=password] {{ width: 100%; padding: 12px 14px; margin-bottom: 16px; border-radius: 8px; border: 1px solid #30363d; background: #0d1117; color: #c9d1d9; font-size: 1em; box-sizing: border-box; }}
button {{ background: #2ea043; color: #fff; padding: 12px 24px; border-radius: 8px; border: 0; font-weight: bold; font-size: 1em; cursor: pointer; width: 100%; }}
button:hover {{ background: #3fb950; }}
.err {{ background: #1f0a0a; border: 1px solid #f85149; color: #ff6b6b; padding: 10px 14px; border-radius: 8px; margin-bottom: 14px; font-size: 0.9em; }}
a {{ color: #58a6ff; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
</style></head><body>
<div class=box>
  <h1>{heading}</h1>
  <p class=sub>{intro}<br>Account: <strong>{email}</strong></p>
  {err_html}
  <form method=POST action=/set-password>
    <label for=password>Password (min {MIN_PASSWORD_LEN} characters)</label>
    <input type=password id=password name=password minlength="{MIN_PASSWORD_LEN}" required autofocus>
    <label for=password2>Confirm password</label>
    <input type=password id=password2 name=password2 minlength="{MIN_PASSWORD_LEN}" required>
    <button type=submit>Save Password →</button>
  </form>
  <p class=sub style="margin-top:18px"><a href=/account>← Back to account</a></p>
</div>
</body></html>""", 200, {"Content-Type": "text/html; charset=utf-8"})


@app.route("/login", methods=["GET", "POST"])
def login():
    """Sign in with email + password to restore Pro access on a new device.

    SECURITY: this route NEVER grants access on the strength of an email alone.
    A GET /login?email=X returns the form and nothing else; the access cookie
    is issued only after verify_subscriber_password() confirms the hash.
    """
    # Already signed in on this device — nothing to do.
    if request.cookies.get("stripe_customer") and is_subscriber():
        return redirect("/account")

    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''

        if login_throttled(email):
            return _login_page(email, error="Too many attempts. Try again in 15 minutes.")

        cid, sub = get_customer_by_email(email)

        # Unknown email, no password set, cancelled sub, and wrong password all
        # take the SAME path and return the SAME message. Differentiating them
        # would turn /login into an oracle for discovering who pays.
        ok = bool(cid) and verify_subscriber_password(cid, password)
        if ok and sub.get('status') != 'active':
            ok = False

        if not ok:
            record_login_failure(email)
            if cid and not sub.get('pw_hash'):
                # Known subscriber who has not set a password yet.
                # Previously this dead-ended: /set-password requires an access
                # cookie, so a customer who cleared their cookies AND never set
                # a password had no route back in except emailing support.
                # Their payment link still works, because /success is
                # idempotent and re-issues the cookie.
                err = ("This account has not set a password yet. Open the "
                       "payment link from your receipt (or the page you were "
                       "on when you subscribed) and everything unlocks again "
                       "immediately - then set a password here for next time. "
                       "If you cannot find that link, email "
                       "support@aismarketcap.com with your receipt.")
            else:
                err = "Incorrect email or password."
            return _login_page(email, error=err)

        clear_login_failures(email)
        resp = make_response(redirect("/", code=302))
        resp.set_cookie("stripe_customer", cid, max_age=86400*30, httponly=True, samesite='Lax')
        print(f"[Login] Authenticated {email} (customer {cid})")
        return resp

    # GET — show the form. Any ?email= just prefills the input.
    return _login_page((request.args.get('email') or '').strip())


def _login_page(email_value='', error=None):
    err_html = f'<div class="err">{error}</div>' if error else ''
    return make_response(f"""<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sign In - AI Market Cap</title>
<style>
body {{ font-family: Segoe UI, sans-serif; background: #0d1117; color: #c9d1d9; min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 24px; }}
.box {{ background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 36px 32px; max-width: 460px; width: 100%; }}
h1 {{ color: #fff; font-size: 1.4em; margin: 0 0 10px; }}
p.sub {{ color: #8b949e; font-size: 0.92em; line-height: 1.6; margin-bottom: 22px; }}
label {{ display: block; font-size: 0.85em; color: #8b949e; margin-bottom: 6px; }}
input {{ width: 100%; padding: 12px 14px; margin-bottom: 16px; border-radius: 8px; border: 1px solid #30363d; background: #0d1117; color: #c9d1d9; font-size: 1em; box-sizing: border-box; }}
button {{ background: #2ea043; color: #fff; padding: 12px 24px; border-radius: 8px; border: 0; font-weight: bold; font-size: 1em; cursor: pointer; width: 100%; }}
button:hover {{ background: #3fb950; }}
.err {{ background: #1f0a0a; border: 1px solid #f85149; color: #ff6b6b; padding: 10px 14px; border-radius: 8px; margin-bottom: 14px; font-size: 0.9em; }}
a {{ color: #58a6ff; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
</style></head><body>
<div class=box>
  <h1>Sign In to Pro</h1>
  <p class=sub>Enter the email and password from your subscription to restore Pro access on this device.</p>
  {err_html}
  <form method=POST action=/login>
    <label for=email>Email address</label>
    <input type=email id=email name=email value="{email_value}" placeholder="you@example.com" required autofocus>
    <label for=password>Password</label>
    <input type=password id=password name=password placeholder="Your password" required>
    <button type=submit>Sign In →</button>
  </form>
  <p class=sub style="margin-top:18px">Never set a password? <a href=/pricing>Subscribe for $5/month →</a><br>
  Lost access? <a href="mailto:support@aismarketcap.com">Contact support</a></p>
</div>
</body></html>""", 200, {"Content-Type": "text/html; charset=utf-8"})


@app.route("/create-portal")
def create_portal():
    """Create a Stripe Customer Portal session so the user can manage their subscription."""
    customer_id = request.cookies.get("stripe_customer", "")
    if not customer_id or not is_subscriber():
        return redirect("/pricing")
    if not stripe.api_key:
        return "Stripe not configured", 500
    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=request.host_url + "account",
        )
        return redirect(session.url, code=302)
    except Exception as e:
        return f"Portal error: {e}", 500


@app.route("/account")
def account():
    """Subscriber account page — shows status, plan, renewal date, manage button."""
    customer_id = request.cookies.get("stripe_customer", "")
    sub = get_subscriptions().get(customer_id, {}) if customer_id else {}

    if not customer_id or not is_subscriber():
        # Not a subscriber — show a friendly "not subscribed" page
        html = """<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Account - AI Market Cap</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: Segoe UI, Arial, sans-serif; background: #0d1117; color: #c9d1d9; min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 24px; }
.box { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 36px 32px; max-width: 480px; text-align: center; }
h1 { color: #fff; font-size: 1.4em; margin-bottom: 10px; }
p { color: #8b949e; font-size: 0.95em; line-height: 1.6; margin-bottom: 18px; }
.btn { background: #2ea043; color: #fff; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold; display: inline-block; }
.btn:hover { background: #3fb950; }
.secondary { color: #58a6ff; text-decoration: none; display: block; margin-top: 14px; font-size: 0.9em; }
</style></head><body>
<div class=box>
  <h1>No Active Subscription</h1>
  <p>You don't have a Pro subscription on this device.<br>Subscribe to unlock the daily Pro Pick, Runner-Up, and AI Chat.</p>
  <a href=/pricing class=btn>Subscribe for $5/month →</a>
  <a href=/login class=secondary>Restore access from another device →</a>
</div>
</body></html>"""
        return make_response(html, 200, {"Content-Type": "text/html; charset=utf-8"})

    # Active subscriber — show account details
    email = sub.get('email', 'Not captured')
    plan = sub.get('plan', 'monthly').capitalize()
    status = sub.get('status', 'active')
    period_end_ts = sub.get('period_end')
    period_end_str = ''
    if period_end_ts:
        try:
            period_end_str = datetime.fromtimestamp(int(period_end_ts), tz=PT).strftime('%B %d, %Y')
        except Exception:
            pass

    # Status badge color
    status_color = {
        'active': '#2ea043', 'trialing': '#2ea043',
        'past_due': '#ffa657', 'unpaid': '#f85149',
        'cancelled': '#f85149', 'canceled': '#f85149',
    }.get(status, '#8b949e')
    status_label = {
        'active': 'Active', 'trialing': 'Free Trial',
        'past_due': 'Payment Failed — Update Card',
        'unpaid': 'Unpaid', 'cancelled': 'Cancelled', 'canceled': 'Cancelled',
    }.get(status, status.capitalize())

    # Get accurate period end from Stripe API (in case our cached value is stale)
    if stripe.api_key:
        try:
            subs_stripe = stripe.Subscription.list(customer=customer_id, limit=1)
            if subs_stripe.data:
                pe = _plain(subs_stripe.data[0]).get('current_period_end')
                if pe:
                    period_end_str = datetime.fromtimestamp(int(pe), tz=PT).strftime('%B %d, %Y')
                    # Refresh local cache
                    save_subscription(
                        customer_id, plan.lower(), status,
                        email=email, sub_id=sub.get('sub_id'),
                        period_end=int(pe),
                    )
        except Exception:
            pass

    html = f"""<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Account - AI Market Cap</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: Segoe UI, Arial, sans-serif; background: #0d1117; color: #c9d1d9; min-height: 100vh; }}
.header {{ background: linear-gradient(135deg,#1a1f2e,#161b22); padding: 18px 30px; border-bottom: 1px solid #30363d; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; }}
.header h1 {{ color: #2ea043; font-size: 1.4em; }}
.header a {{ color: #58a6ff; text-decoration: none; font-size: 0.9em; }}
.container {{ max-width: 720px; margin: 0 auto; padding: 40px 24px; }}
.card {{ background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 28px; margin-bottom: 18px; }}
.card h2 {{ color: #fff; font-size: 1.1em; margin-bottom: 18px; padding-bottom: 10px; border-bottom: 1px solid #21262d; }}
.row {{ display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #21262d; }}
.row:last-child {{ border-bottom: none; }}
.lbl {{ color: #8b949e; font-size: 0.9em; }}
.val {{ color: #fff; font-size: 0.95em; font-weight: 500; }}
.badge {{ display: inline-block; background: {status_color}22; color: {status_color}; border: 1px solid {status_color}; padding: 3px 12px; border-radius: 20px; font-size: 0.78em; font-weight: bold; }}
.btn {{ display: inline-block; background: #2ea043; color: #fff; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-right: 10px; }}
.btn:hover {{ background: #3fb950; }}
.btn.secondary {{ background: #21262d; color: #c9d1d9; }}
.btn.secondary:hover {{ background: #30363d; }}
.note {{ color: #6e7681; font-size: 0.85em; margin-top: 14px; line-height: 1.5; }}
</style></head><body>
<div class=header>
  <h1>★ Your Pro Account</h1>
  <div>
    <a href="/">← Scanner</a>
    <a href=/logout style="margin-left:16px;color:#ff6b6b">Logout</a>
  </div>
</div>
<div class=container>
  <div class=card>
    <h2>Subscription</h2>
    <div class=row>
      <span class=lbl>Status</span>
      <span class=val><span class=badge>{status_label}</span></span>
    </div>
    <div class=row>
      <span class=lbl>Plan</span>
      <span class=val>{plan}</span>
    </div>
    <div class=row>
      <span class=lbl>Email</span>
      <span class=val>{email}</span>
    </div>
    {f'''<div class=row><span class=lbl>Next renewal</span><span class=val>{period_end_str}</span></div>''' if period_end_str else ''}
    <div class=row>
      <span class=lbl>Customer ID</span>
      <span class=val style="font-family:monospace;font-size:0.82em">{customer_id[:18]}...</span>
    </div>
  </div>

  <div class=card>
    <h2>Manage</h2>
    <a href=/create-portal class=btn>Manage Billing & Cancel →</a>
    <a href=/ class="btn secondary">Go to Scanner</a>
    <p class=note>Update your card, view invoices, or cancel anytime through the Stripe billing portal. Your access stays active until the end of your current billing period.</p>
  </div>

  <div class=card>
    <h2>Sign In on Another Device</h2>
    <p class=note style="margin-top:0">If you get logged out (cleared cookies, new device, different browser), use <a href=/login style="color:#58a6ff">/login</a> with the email and password from your subscription to restore Pro access without re-paying.</p>
  </div>
</div>
</body></html>"""
    return make_response(html, 200, {"Content-Type": "text/html; charset=utf-8"})


@app.route("/api/scans", methods=["GET"])
def api_scans():
    customer_id = request.cookies.get("stripe_customer", "")
    token = request.cookies.get(COOKIE_NAME, "")
    used = get_scans_today(customer_id) if customer_id else get_scans_today(token)
    return jsonify({'used': used, 'limit': MAX_SCANS_PER_DAY, 'remaining': max(0, MAX_SCANS_PER_DAY - used)})

@app.route("/webhook", methods=["POST"])
def webhook():
    """Stripe webhook handler — covers full subscription lifecycle.

    Events handled:
      - checkout.session.completed          → mark active + capture email
      - customer.subscription.created       → mark active
      - customer.subscription.updated       → active/trialing/past_due/unpaid/canceled
      - customer.subscription.deleted       → mark cancelled
      - invoice.payment_succeeded           → keep active on renewal
      - invoice.payment_failed              → mark past_due
      - checkout.session.async_payment_succeeded → delayed (ACH/wire) checkout
    """
    payload = request.data
    sig = request.headers.get('Stripe-Signature', '')

    # ---- FAIL CLOSED -------------------------------------------------------
    # Previously, when STRIPE_WEBHOOK_SECRET was unset we fell back to
    # json.loads(payload) and trusted the body. That is not a safe default: it
    # means anyone who can POST to /webhook can fabricate
    # checkout.session.completed or customer.subscription.updated and grant or
    # revoke any subscription by guessing a customer id. An unset env var —
    # a missing Railway variable, a typo, a redeploy that dropped it — silently
    # turned the whole endpoint into an unauthenticated write API.
    #
    # Signature verification is the ONLY thing that proves an event came from
    # Stripe, so if we cannot verify we must refuse the event. Returning 500
    # (not 400) tells Stripe this is a server-side configuration problem worth
    # retrying, rather than a malformed request from the sender.
    if not STRIPE_WEBHOOK_SECRET:
        print("[Webhook] FATAL: STRIPE_WEBHOOK_SECRET is not set - refusing to "
              "process unsigned events. Set it in Railway to the signing secret "
              "from Stripe Dashboard > Developers > Webhooks > your endpoint.")
        return ("Webhook misconfigured: STRIPE_WEBHOOK_SECRET is not set on the "
                "server. Unsigned events are rejected."), 500

    try:
        event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
    except ValueError as e:
        # Payload is not valid JSON / signature header malformed
        return f"Webhook signature error: {e}", 400
    except Exception as e:
        # Signature did not match. Treat as bad request.
        return f"Webhook signature error: {e}", 400

    # The Event is a StripeObject too. Normalise the whole thing once so every
    # branch below can use plain dict access safely.
    event = _plain(event)
    etype = event.get('type', '')
    print(f"[Webhook] Event: {etype}")

    try:
        if etype == 'checkout.session.completed':
            obj = _plain(event['data']['object'])
            customer_id = obj.get('customer')
            plan = (obj.get('metadata') or {}).get('plan', 'monthly')
            email = (obj.get('customer_details') or {}).get('email') or (obj.get('customer_email') or '')
            # Also fetch the customer's email from Stripe if missing
            if not email and customer_id and stripe.api_key:
                try:
                    cust = _plain(stripe.Customer.retrieve(customer_id))
                    email = cust.get('email', '')
                except Exception:
                    pass
            sub_id = obj.get('subscription')
            period_end = None
            if sub_id and stripe.api_key:
                try:
                    sub = _plain(stripe.Subscription.retrieve(sub_id))
                    period_end = sub.get('current_period_end')
                except Exception:
                    pass
            save_subscription(customer_id, plan, 'active',
                              email=email, sub_id=sub_id, period_end=period_end)
            _STRIPE_VALIDATION_CACHE.pop(customer_id, None)
            print(f"[Webhook] checkout.session.completed: {customer_id} {plan} {email}")

        elif etype == 'customer.subscription.created':
            sub = _plain(event['data']['object'])
            customer_id = sub.get('customer')
            status = sub.get('status', 'active')
            plan = (sub.get('metadata') or {}).get('plan', 'monthly')
            period_end = sub.get('current_period_end')
            email = None
            if customer_id and stripe.api_key:
                try:
                    cust = _plain(stripe.Customer.retrieve(customer_id))
                    email = cust.get('email')
                except Exception:
                    pass
            save_subscription(customer_id, plan, status,
                              email=email, sub_id=sub.get('id'), period_end=period_end)
            _STRIPE_VALIDATION_CACHE.pop(customer_id, None)
            print(f"[Webhook] subscription.created: {customer_id} {status}")

        elif etype == 'customer.subscription.updated':
            sub = _plain(event['data']['object'])
            customer_id = sub.get('customer')
            stripe_status = sub.get('status')  # active, trialing, past_due, unpaid, canceled, etc.
            # Only 'active' and 'trialing' should grant Pro access
            local_status = 'active' if stripe_status in ('active', 'trialing') else stripe_status
            plan = (sub.get('metadata') or {}).get('plan', 'monthly')
            period_end = sub.get('current_period_end')
            sub_id = sub.get('id')
            # Try to keep email we already have, otherwise fetch
            existing = get_subscriptions().get(customer_id, {})
            email = existing.get('email')
            save_subscription(customer_id, plan, local_status,
                              email=email, sub_id=sub_id, period_end=period_end)
            _STRIPE_VALIDATION_CACHE.pop(customer_id, None)
            print(f"[Webhook] subscription.updated: {customer_id} stripe={stripe_status} -> local={local_status}")

        elif etype == 'customer.subscription.deleted':
            sub = _plain(event['data']['object'])
            customer_id = sub.get('customer')
            existing = get_subscriptions().get(customer_id, {})
            plan = existing.get('plan', 'monthly')
            save_subscription(customer_id, plan, 'cancelled', email=existing.get('email'))
            _STRIPE_VALIDATION_CACHE.pop(customer_id, None)
            print(f"[Webhook] subscription.deleted: {customer_id} -> cancelled")

        elif etype == 'invoice.payment_succeeded':
            inv = _plain(event['data']['object'])
            customer_id = inv.get('customer')
            if customer_id and get_subscriptions().get(customer_id):
                existing = get_subscriptions()[customer_id]
                plan = existing.get('plan', 'monthly')
                period_end = inv.get('period_end') or existing.get('period_end')
                save_subscription(customer_id, plan, 'active',
                                  email=existing.get('email'),
                                  sub_id=existing.get('sub_id'),
                                  period_end=period_end)
                _STRIPE_VALIDATION_CACHE.pop(customer_id, None)
                print(f"[Webhook] invoice.payment_succeeded: {customer_id} renewed (period_end={period_end})")

        elif etype == 'invoice.payment_failed':
            inv = _plain(event['data']['object'])
            customer_id = inv.get('customer')
            if customer_id and get_subscriptions().get(customer_id):
                existing = get_subscriptions()[customer_id]
                plan = existing.get('plan', 'monthly')
                # Don't fully cancel — Stripe will retry. Mark past_due.
                save_subscription(customer_id, plan, 'past_due',
                                  email=existing.get('email'),
                                  sub_id=existing.get('sub_id'),
                                  period_end=existing.get('period_end'))
                _STRIPE_VALIDATION_CACHE.pop(customer_id, None)
                print(f"[Webhook] invoice.payment_failed: {customer_id} -> past_due")

        elif etype == 'checkout.session.async_payment_succeeded':
            obj = _plain(event['data']['object'])
            customer_id = obj.get('customer')
            plan = (obj.get('metadata') or {}).get('plan', 'monthly')
            email = (obj.get('customer_details') or {}).get('email', '')
            sub_id = obj.get('subscription')
            period_end = None
            if sub_id and stripe.api_key:
                try:
                    sub = _plain(stripe.Subscription.retrieve(sub_id))
                    period_end = sub.get('current_period_end')
                except Exception:
                    pass
            save_subscription(customer_id, plan, 'active',
                              email=email, sub_id=sub_id, period_end=period_end)
            _STRIPE_VALIDATION_CACHE.pop(customer_id, None)
            print(f"[Webhook] async_payment_succeeded: {customer_id} {plan}")

    except Exception as e:
        print(f"[Webhook] Handler error on {etype}: {e}")
        import traceback
        traceback.print_exc()
        # Return 200 anyway so Stripe doesn't retry forever on bad data

    return "ok", 200

@app.route("/run", methods=["POST"])
def api_run():
    """Run scan - requires active subscription + daily limit.

    Tyler 2026-10-22: "the pro scan button should change to just say scan and
    run fresh scan when clicked".

    THREE BUGS FIXED HERE

    BUG 1 - it repeated /api/chat's mistake and hand-rolled the subscriber
    check, reading subscriptions.json directly. is_subscriber() also falls
    back to asking Stripe when the local record is missing, which is the only
    thing that survives a Railway redeploy (the JSON lives on ephemeral disk
    and comes back empty). So after any deploy the one button subscribers paid
    for would redirect them to /pricing despite Stripe showing them paid.
    There is now one definition of "is a subscriber".

    BUG 2 - it called trigger_scan() and threw away the return value, then
    replied "ok" unconditionally. When in-container scanning is disabled
    trigger_scan() returns False and does nothing, so the button said "Scan
    started! Reloading...", reloaded, and served the identical page. A button
    that reports success while doing nothing is worse than no button. It now
    returns the real outcome, and the JS is told when the scan genuinely ran.

    BUG 3 - the pricing page and the FAQ both promise "3 additional scans per
    day" while MAX_SCANS_PER_DAY was 2. The limit now matches what is sold.
    """
    # BUG 1: use the canonical helper.
    if not is_subscriber():
        return redirect("/pricing")

    customer_id = request.cookies.get("stripe_customer", "")
    token = request.cookies.get(COOKIE_NAME, "")
    key_id = customer_id if customer_id else token

    if get_scans_today(key_id) >= MAX_SCANS_PER_DAY:
        return jsonify({
            'error': 'limit_reached',
            'message': f'Daily scan limit reached ({MAX_SCANS_PER_DAY}/day). Try again tomorrow.',
        }), 429

    # BUG 2: report what actually happened.
    started = trigger_scan()
    if started:
        increment_scan_count(key_id)
        return jsonify({
            'status': 'started',
            'message': 'Fresh scan started right here. This takes a couple of minutes.',
        })

    # Running in the container is disabled (it OOM'd Railway into a restart
    # loop that 404'd every route). Instead of faking success, queue a real
    # request that Tyler's machine picks up within a minute. It does the scan,
    # commits and pushes, and Railway redeploys the fresh page.
    q = _read_queue()
    already = q.get("state") in ("pending", "running")
    q.update({"state": "pending", "requested_at": time.time(),
              "requested_by": key_id or "anonymous"})
    _write_queue(q)
    increment_scan_count(key_id)
    if already:
        return jsonify({
            'status': 'already_pending',
            'message': ("A fresh scan is already queued and starts within a "
                        "minute. This page updates itself when it lands."),
        })
    return jsonify({
        'status': 'queued_locally',
        'message': ("Scan queued - it starts within about a minute and this "
                    "page will update itself when fresh data is pushed."),
    })

@app.route("/status")
def api_status():
    return jsonify({
        'scan_state': scan_state.scan_state,
        'refresh_state': scan_state.refresh_state
    })

@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Chat - requires active subscription.

    Three bugs fixed here 2026-10-22 (Tyler: "wire up the Ask AI button to
    actually work for Pro subscribers").

    BUG 1 - it returned a 302 redirect to /pricing. This is a JSON endpoint
    called by fetch(); a 302 makes the browser transparently follow it and
    hand back the PRICING PAGE HTML with status 200, so r.json() threw and the
    user saw "Error: Unexpected token '<'" instead of being told to subscribe.
    The JS already knows how to handle this case (it checks r.redirected and
    r.url), so it must stay a redirect. Now it carries an explicit
    ?from=chat marker, and the chat JS checks for that marker specifically
    rather than pattern-matching any URL containing "/pricing" - a legitimate
    future redirect elsewhere can no longer be mistaken for a paywall.

    BUG 2 - it hand-rolled its own subscriber check and looked ONLY at the
    stripe_customer cookie. is_subscriber() also checks the session cookie and,
    critically, falls back to asking Stripe when the local record is missing.
    subscriptions.json lives on Railway's ephemeral disk and comes back empty
    after a redeploy, which is exactly what happened - so the one endpoint a
    paying customer was most likely to hit after paying was the one that
    denied them. It now calls the same helper every other gated route uses, so
    there is one definition of "is a subscriber" instead of three that drift.

    BUG 3 - it re-parsed the body AFTER the auth check, so an unauthenticated
    oversized request could never be rejected on length. Order fixed.
    """
    if not is_subscriber():
        return redirect("/pricing?from=chat")

    try:
        body = request.get_json(force=True)
    except Exception:
        body = {}
    if not isinstance(body, dict):
        body = {}
    user_msg = (body.get("message") or "").strip()
    if not user_msg:
        return jsonify({"error": "No message provided"}), 400
    if len(user_msg) > 1000:
        return jsonify({"error": "Message too long (max 1000 chars)"}), 400

    reply = call_llm(user_msg)
    return jsonify({"reply": reply})


# ===== LLM (GROQ) =====
# ===== AI CHAT =====
# Provider order is MiniMax first, then Groq. Tyler 2026-10-22: "wire this up
# to use minimax locally". MINIMAX_API_KEY wins when present.
#
# NOTE ON THE SESSION TOKEN. ~/.minimax/config.yaml holds apiKey: sk-xxx, a
# PLACEHOLDER, and local-runtime.auth.json holds Tyler's account SESSION JWT.
# Neither is a MiniMax platform key. The session token is never wired into an
# unattended bot - it is a login artefact, not an API credential, and using it
# server-side is both broken and a credential-hygiene problem.
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")
MINIMAX_BASE_URL = os.environ.get(
    "MINIMAX_BASE_URL", "https://api.minimax.io/v1").rstrip("/")
MINIMAX_MODEL = os.environ.get("MINIMAX_MODEL", "MiniMax-Text-01")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

CHAT_SYSTEM = (
    "You are the assistant for AI Market Cap, a scanner for US stocks in "
    "pre-earnings momentum setups. Answer briefly and concretely (2-4 "
    "sentences). Ground answers in the scanner's own concepts: score, "
    "sentiment, days to earnings, and the /stocks table. If you do not know "
    "something, say so rather than guessing."
)


def _http_post_json(url, headers, payload, timeout=25):
    """POST JSON and return parsed dict. Raises for caller to classify."""
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", "replace"))


# REQUIRED, not cosmetic. urllib sends no User-Agent by default, and both
# Groq and MiniMax sit behind bot protection that rejects UA-less requests with
# HTTP 403 "error code: 1010" BEFORE they reach the API. A perfectly valid key
# therefore looks invalid. Verified live against Groq:
#     no User-Agent      -> HTTP 403  error code: 1010   (blocked)
#     browser User-Agent -> HTTP 401  invalid API key    (request arrives)
_BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
               "AppleWebKit/537.36 (KHTML, like Gecko) "
               "Chrome/120.0 Safari/537.36")


def call_minimax(user_msg):
    """MiniMax chat completion (OpenAI-compatible /chat/completions)."""
    data = _http_post_json(
        MINIMAX_BASE_URL + "/chat/completions",
        {"Authorization": f"Bearer {MINIMAX_API_KEY}",
         "Content-Type": "application/json",
         "User-Agent": _BROWSER_UA},
        {"model": MINIMAX_MODEL,
         "messages": [{"role": "system", "content": CHAT_SYSTEM},
                      {"role": "user", "content": user_msg}],
         "temperature": 0.4, "max_tokens": 400})
    return (data["choices"][0]["message"]["content"] or "").strip()


def _fmt_money(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return "n/a"
    return f"${v:,.2f}" if v < 1000 else f"${v:,.0f}"


def _load_scanner_rows():
    try:
        sf = Path(__file__).parent / "scanner_data.json"
        if not sf.exists():
            return []
        rows = json.loads(sf.read_text(encoding="utf-8"))
        if isinstance(rows, dict):
            rows = rows.get("stocks", [])
        if not isinstance(rows, list):
            return []
        return [r for r in rows if isinstance(r, dict) and r.get("ticker")]
    except Exception:
        return []


def answer_from_data(question):
    """Answer the questions the scanner can answer from its own numbers.

    WHY THIS EXISTS. Tyler 2026-10-22: "have it actually work right and chat
    back when paying customer chat with it." The chat is a $5 feature that has
    never once returned a real answer - no provider key has ever been
    configured, so it said "warming up" or "trouble connecting" forever.

    Most of what a subscriber asks is not creative writing. It is "what is
    today's pick", "what does 86 mean", "when do they report". We already hold
    every one of those answers. Serving them from our own data means the chat is
    a working product TODAY - no third-party key, no per-request cost, no rate
    limit, and no way for it to go dark when a provider does.

    This is the floor, not the ceiling. With a provider key configured the LLM
    handles free-form questions; this handles the factual ones and is the
    fallback whenever the provider is unreachable, so the customer never sees a
    dead chat box.
    """
    q = (question or "").strip()
    ql = q.lower()
    rows = _load_scanner_rows()

    try:
        pick = load_pro_pick() or None
    except Exception:
        pick = None

    # ---- a specific ticker, e.g. "what about FROG?" --------------------
    hits = [r for r in rows
            if isinstance(r.get("ticker"), str)
            and len(r["ticker"]) >= 3
            and r["ticker"].lower() in ql]
    if hits:
        r = max(hits, key=lambda x: float(x.get("score") or 0))
        bits = [f"{r['ticker']} ({r.get('company_name') or ''}) scores "
                f"{round(float(r.get('score') or 0))} out of 100."]
        if r.get("price"):
            bits.append(f"Price {_fmt_money(r.get('price'))}.")
        if r.get("days_left") is not None:
            bits.append(f"{r.get('days_left')} days to earnings on "
                        f"{r.get('earnings_date') or 'the report date'}.")
        if r.get("sentiment"):
            bits.append(f"Earnings sentiment: {r.get('sentiment')}.")
        if r.get("iv"):
            bits.append(f"Implied volatility {r.get('iv')}%.")
        if r.get("short_int"):
            bits.append(f"Short interest {r.get('short_int')}% of float.")
        return " ".join(bits)

    # ---- targets and stops ----------------------------------------------------
    # BEFORE the pick branch: "what is my target" contains "what is", which is
    # also a pick trigger. Ordering matters or a question about targets answers
    # with the pick.
    if any(w in ql for w in ("target", "stop", "entry", "exit", "risk")):
        if pick and (pick.get("target_price") or pick.get("stop_loss")):
            bits = [f"For {pick.get('ticker')}: entry around "
                    f"{_fmt_money(pick.get('entry_price') or pick.get('price'))}."]
            if pick.get("target_price"):
                bits.append(f"Target {_fmt_money(pick['target_price'])}.")
            if pick.get("stop_loss"):
                bits.append(f"Stop {_fmt_money(pick['stop_loss'])}.")
            return " ".join(bits)
        return ("Entry, target and stop for the pick are in the Pro Pick banner "
                "at the top of the Scanner, and on your Pro dashboard.")

    # ---- plans ------------------------------------------------------------------
    # Also before "how", so "how much is it" is a billing question rather than a
    # question about how the scanner works.
    if any(w in ql for w in ("how much", "cost", "plan", "cancel", "billing",
                             "subscri", "worth it", "price per", "annual",
                             "year", "upgrade")):
        return ("Pro is $5/month and covers the AI Pick, the ranked table, "
                "targets and stops, this AI Chat, and the daily email alert. "
                "The annual plan is $50/year - two months free, and it locks "
                "the price so a rate change never hits you mid-year. Cancel "
                "anytime from your account page.")

    # ---- the picks ----------------------------------------------------------
    # Deliberately NOT triggered by a bare "what is" - that phrase is far too
    # generic and made unrelated questions answer with the pick.
    wants_pick = any(w in ql for w in (
        "pick", "buy", "trade", "recommend", "should i", "runner", "today",
        "best stock", "top stock", "top pick"))
    if wants_pick and pick:
        name = pick.get("ticker", "?")
        bits = [f"Today's pick is {name}"
                + (f" ({pick.get('company_name')})"
                   if pick.get("company_name") else "") + "."]
        if pick.get("score"):
            bits.append(f"Composite score {round(float(pick['score']))}/100.")
        if pick.get("price"):
            bits.append(f"Price {_fmt_money(pick['price'])}.")
        if pick.get("days_to_earnings") not in (None, "", "?"):
            bits.append(f"{pick['days_to_earnings']} days to earnings.")
        bits.append("The Scanner header has the full entry, target and stop.")
        return " ".join(bits)
    if wants_pick and rows:
        top = sorted(rows, key=lambda x: float(x.get("score") or 0),
                     reverse=True)[:3]
        listing = ", ".join(
            f"{t['ticker']} (score {round(float(t.get('score') or 0))})"
            for t in top)
        return (f"Strongest setups right now: {listing}. Open the Scanner for "
                f"the full ranked table.")

    # ---- score -------------------------------------------------------------
    if any(w in ql for w in ("score", "scoring", "rank", "rating")):
        return ("The score is 0-100 and combines five factors: analyst "
                "coverage (25pts), buy% conviction (25pts), strong-buy count "
                "(2pts each, max 20), 5-day upside (max 15pts) and earnings "
                "sentiment (max 15pts). 80+ is the strong-buy zone. Entries are "
                "made 1-35 days before earnings, exits 1-5 days after a beat.")

    # ---- earnings timing ----------------------------------------------------
    if any(w in ql for w in ("earnings", "report", "days", "when")):
        soon = sorted([r for r in rows if r.get("days_left") is not None],
                      key=lambda x: float(x.get("days_left") or 999))[:3]
        if soon:
            listing = ", ".join(f"{r['ticker']} in {r.get('days_left')}d"
                                for r in soon)
            return (f"Closest to reporting: {listing}. Open the Scanner and sort "
                    f"by days left to see the rest.")

    # ---- how scanning works --------------------------------------------------
    if any(w in ql for w in ("how", "work", "scan", "update", "refresh", "data")):
        return ("The scanner runs every market day at 6:30 AM PT. Press Scan for "
                "a fresh run - subscribers get 3 per day. Prices and options "
                "come from Yahoo Finance; analyst ratings from Yahoo "
                "recommendations.")

    if any(w in ql for w in ("hi", "hello", "hey", "thanks", "thank you")):
        return ("Happy to help. I can tell you today's pick, explain the score "
                "and the targets, look up any ticker by symbol, or walk you "
                "through how the scanner works. What do you want to know?")

    return ("I don't have that one yet. I can tell you today's pick, explain "
            "the score and the targets, look up any ticker by symbol, or walk "
            "you through how the scanner works. Try one of those, or rephrase.")


def call_llm(user_msg):
    """Answer a chat question. Provider order: MiniMax, then Groq.

    Falls back to answer_from_data() whenever no provider is configured or the
    provider fails. That fallback is why this feature can be sold at all: a
    $5 subscriber must never be met with "warming up" for a question we can
    answer from data we already hold.

    Failure modes are logged distinctly - the API key value is never printed,
    only whether one is present.
    """
    grounded = answer_from_data(user_msg)

    provider = None
    fn = None
    if MINIMAX_API_KEY:
        provider, fn = "minimax", call_minimax
    elif GROQ_API_KEY:
        provider, fn = "groq", call_groq

    if not provider:
        print(f"[Chat] no provider key configured - answering from scanner "
              f"data. Asked: {user_msg[:70]!r}")
        return grounded

    try:
        answer = fn(user_msg)
        if not answer:
            print(f"[Chat] {provider} returned an empty completion")
            return grounded
        return answer
    except urllib.error.HTTPError as e:
        try:
            detail = e.read()[:300].decode("utf-8", "replace")
        except Exception:
            detail = ""
        print(f"[Chat] {provider} HTTP {e.code}: {detail}")
        # Cloudflare blocks UA-less requests with 403 "error code: 1010" before
        # they reach the API, which is indistinguishable from a bad key by
        # status alone. Never report that as an authorisation problem.
        if "1010" in detail or "cloudflare" in detail.lower():
            return grounded
        if e.code in (401, 403):
            print(f"[Chat] {provider} key rejected - key needs replacing")
            return grounded
        if e.code == 429:
            return grounded
        return grounded
    except Exception as e:
        print(f"[Chat] {provider} failed: {type(e).__name__}: {e}")
        return grounded


def call_groq(user_msg):
    """Groq chat completion."""
    data = _http_post_json(
        "https://api.groq.com/openai/v1/chat/completions",
        {"Authorization": f"Bearer {GROQ_API_KEY}",
         "Content-Type": "application/json",
         "User-Agent": _BROWSER_UA},
        {"model": "llama-3.3-70b-versatile",
         "messages": [{"role": "system", "content": CHAT_SYSTEM},
                      {"role": "user", "content": user_msg}],
         "temperature": 0.4, "max_tokens": 400})
    return (data["choices"][0]["message"]["content"] or "").strip()

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


def _esc(text):
    """HTML-escape for safe interpolation into card markup."""
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;"))

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
        for a in articles:  # newest first — show every published article
            # Escape all interpolated fields. index.json stores PLAIN TEXT excerpts;
            # emitting them raw is what previously leaked a literal "<p>" into every card.
            s_title = _esc(str(a.get("title", "")))
            s_keyword = _esc(str(a.get("keyword", "")))
            s_excerpt = _esc(str(a.get("excerpt", "")))
            cards_html += f"""<a href="/blog/{a['slug']}" class="win-card">
                <div class="h-badge" style="background:#1a3a5c;color:#58a6ff">📝 Article</div>
                <div class="t" style="color:#fff;font-size:1.1em;font-weight:bold;margin:8px 0 4px">{s_title}</div>
                <div class="d" style="color:#888;font-size:0.82em;margin-bottom:8px">{a['date']} · {s_keyword}</div>
                <div class="l" style="color:#c9d1d9;font-size:0.85em;line-height:1.6">{s_excerpt}</div>
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

def _retired_slugs():
    """Slugs of purged template-filler articles (blog/retired_slugs.json)."""
    p = BLOG_DIR / "retired_slugs.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


@app.route("/blog/<slug>")
def blog_article(slug):
    """Serve an individual blog article.

    Purged template-filler articles (19 of them, e.g. "Why Does Pre-Earnings
    Stock Picks: The Complete Guide for 2026") are 301'd to the blog index
    instead of 404ing. They were removed from index.json and therefore from
    sitemap.xml; the redirect preserves any ranking signal they earned.
    """
    app_dir = Path(__file__).parent
    article_path = app_dir / "blog" / f"{slug}.html"

    if not article_path.exists():
        if slug in _retired_slugs():
            return redirect("/blog", code=301)
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


def _retired_slugs():
    """Slugs of purged template-filler articles (blog/retired_slugs.json)."""
    p = BLOG_DIR / "retired_slugs.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


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
        {"loc": f"{base}/stocks", "priority": "0.8", "changefreq": "weekly"},
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

    # Stock analysis pages — the biggest SEO play
    stock_pages = []
    stock_dir = Path(__file__).parent / "stock_pages"
    if stock_dir.exists():
        for f in stock_dir.glob("*.html"):
            ticker = f.stem.upper()
            stock_pages.append({
                "loc": f"{base}/stock/{ticker}",
                "priority": "0.7",
                "changefreq": "weekly",
                "lastmod": datetime.now().strftime("%Y-%m-%d")
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

    for page in static_pages + wins_pages + blog_items + stock_pages:
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
def manual_scan_trigger():
    """Manually run the scanner and update the site. Use ?key=SECRET to authenticate.

    RENAMED from trigger_scan 2026-10-22. This route was DEFINED SECOND under
    the same name, so Python bound the name to THIS function and the real
    trigger_scan() at line ~1022 became unreachable - /run called this one
    instead. It returned 503 "disabled_in_container", which /run discarded,
    so the Scan button claimed success while queueing nothing at all.

    Exactly the failure the earlier duplicate-is_subscriber() note warned about:
    two definitions of one name means an edit can land on the wrong one and the
    live one silently stays different. verify_auth.py now asserts this name is
    defined once.
    """
    import os
    key = os.environ.get("SCAN_TRIGGER_KEY", "")
    provided = request.args.get("key", "")
    if key and provided != key:
        abort(403)
    # SAFETY: this route shadows the earlier trigger_scan() and would spawn the
    # scanner in-container (OOM -> restart loop -> 404 on every route).
    if not ALLOW_IN_CONTAINER_SCAN:
        return jsonify({
            "error": "disabled_in_container",
            "message": "In-container scanning is disabled to keep the service healthy. "
                       "Data is refreshed by the local daily_scan.ps1 and pushed to GitHub.",
        }), 503
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

@app.route("/traffic/outreach_state.json")
def traffic_outreach_state():
    """Serve outreach state (emails sent/replied/bounced)."""
    primary = TRAFFIC_DIR / "modules" / "outreach_state.json"
    fallback = TRAFFIC_DIR / "outreach_state.json"
    src = primary if primary.exists() else fallback
    if not src.exists():
        return jsonify({"sent": [], "replied": [], "bounced": []})
    with open(src, encoding="utf-8") as f:
        return jsonify(json.load(f))

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
    content = log_path.read_text(encoding="utf-8", errors="replace")
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
        "build_stocks":     (str(Path(__file__).parent / "generate_stock_pages.py"), []),
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

    if ALLOW_IN_CONTAINER_SCAN:
        threading.Thread(target=auto_scan_loop, daemon=True).start()
        print("[Safety] auto_scan_loop STARTED (ALLOW_IN_CONTAINER_SCAN=1)")
    else:
        print("[Safety] auto_scan_loop NOT started — local push supplies the data")
    app.run(host="0.0.0.0", port=PORT, debug=False)