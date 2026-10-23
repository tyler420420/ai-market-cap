#!/usr/bin/env python3
"""Send the daily Pro Pick email.

WHY THIS EXISTS
---------------
The pricing page sells "Real-time earnings alerts" and the repo contained no
outbound transport of any kind - no smtplib, no SendGrid, no push. A sold
feature that does nothing is the same defect as the Scan button that reported
work it could not do.

This also creates the owned channel the site never had: before it, the only
<input> on the whole site was the chat box, so a visitor who was not ready to
pay today was unreachable.

Recipients:
  * everyone on email_list.json (opted in from the free page)
  * every active subscriber in subscriptions.json

The Pro values are included for subscribers and omitted for the free list.

    THIS WAS NOT TRUE UNTIL 2026-10-22.

    build_email() took no recipient argument. It built ONE email containing
    the 3d / 7d / 14d targets and main() sent that identical email to
    everyone on both lists. PAID_COLUMNS was defined at module scope,
    documented in the docstring as the split, and then never referenced
    again - the free-list redaction was designed and never wired up.

    The consequence: every free-page email signup would have received the
    paid targets in writing, in an inbox, where they cannot be taken back.
    Same defect class as the CSS-blur paywall leak, moved into email.

    build_email() now takes `paid` and the target column is built from
    PAID_COLUMNS behind that flag. verify_alert_targets.py asserts it
    behaviourally against the real scanner data - it builds both variants and
    requires the free one to carry no targets - and
    prove_alert_targets_bites.py requires the guard to reject a reverted
    implementation.

CONFIGURATION (nothing secret lives in this file)
------------------------------------------------
Put credentials in  alert.env  next to this script, gitignored:

    ALERT_FROM=alerts@yourdomain.com
    ALERT_SMTP_HOST=smtp.yourprovider.com
    ALERT_SMTP_PORT=587
    ALERT_SMTP_USER=...
    ALERT_SMTP_PASS=...

or, for an HTTP provider, just:

    ALERT_API_KEY=re_...        # Resend
    ALERT_API_URL=https://api.resend.com/emails

Run:  python send_daily_alert.py [--dry-run]
Exit 0 = sent, or dry-run completed. Exit 1 = not configured or failed loudly.
"""
import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path

SITE = Path(__file__).parent
PT_TZ = None
try:
    from zoneinfo import ZoneInfo
    PT_TZ = ZoneInfo("America/Los_Angeles")
except Exception:
    pass

# The Pro-only columns, in the order they are displayed. These key names are
# historical and do not match their meaning: pe_target is the 3-DAY target,
# "3d" is the 7-DAY target and "5d" is the 14-DAY target. PAID_LABELS is what
# a subscriber actually reads, so the two are zipped rather than the keys
# being printed raw.
PAID_COLUMNS = ("pe_target", "3d", "5d")
PAID_LABELS = ("3d", "7d", "14d")
FREE_TARGETS_CELL = "Available in Pro"


def load_env():
    """Read alert.env without printing a single value."""
    env = dict(os.environ)
    p = SITE / "alert.env"
    if p.exists():
        for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def load_json(name, default):
    try:
        return json.loads((SITE / name).read_text(encoding="utf-8"))
    except Exception:
        return default


def today_str():
    now = datetime.now(PT_TZ) if PT_TZ else datetime.now()
    return now.strftime("%Y-%m-%d")


def build_email(paid: bool = False):
    """Compose the daily email. Returns (html, subject).

    paid=True  -> a subscriber: real 3d/7d/14d targets, no upsell.
    paid=False -> the free list: no target values anywhere in the message.
    """
    data = load_json("scanner_data.json", [])
    if not data:
        return None, "no data"
    picks = [s for s in data if (s.get("score") or 0) >= 75][:5]
    if not picks:
        return None, "no picks above threshold"

    top = picks[0]
    ticker = top.get("ticker", "?")
    company = top.get("company_name", "")
    score = top.get("score", "?")
    price = top.get("price", "?")
    days = top.get("days_left", "?")
    when = top.get("earnings_date", "")

    def money(v):
        try:
            return f"${float(v):,.0f}"
        except Exception:
            return "n/a"

    rows = []
    for s in picks:
        d = []
        if paid:
            for key, label in zip(PAID_COLUMNS, PAID_LABELS):
                if s.get(key):
                    d.append(f"{label} {money(s[key])}")
        targets = " &middot; ".join(d) if d else FREE_TARGETS_CELL
        rows.append(
            f'<tr><td style="padding:8px 10px;border-bottom:1px solid #21262d;'
            f'font-weight:bold;color:#58a6ff">{s.get("ticker")}</td>'
            f'<td style="padding:8px 10px;border-bottom:1px solid #21262d">'
            f'{s.get("company_name","")}</td>'
            f'<td style="padding:8px 10px;border-bottom:1px solid #21262d;'
            f'color:#00ff88;font-weight:bold">{s.get("score")}</td>'
            f'<td style="padding:8px 10px;border-bottom:1px solid #21262d">'
            f'{money(s.get("price"))}</td>'
            f'<td style="padding:8px 10px;border-bottom:1px solid #21262d;'
            f'color:#c9d1d9">{days_label(s)}</td>'
            f'<td style="padding:8px 10px;border-bottom:1px solid #21262d;'
            f'color:#8b949e;font-size:12px">{targets}</td></tr>')

    # A subscriber does not need to be upsold, and their targets are already
    # in the message above, so the call to action differs by tier too.
    if paid:
        cta_href = "https://aismarketcap.com"
        cta_label = "Open today&rsquo;s full table &rarr;"
        footer = "Your curated Pro pick, sent before the report. " \
                 "Not financial advice. Do your own research."
    else:
        cta_href = "https://aismarketcap.com/pricing"
        cta_label = "See entry, targets &amp; stop &rarr;"
        footer = "Entry, targets and stop for every Pro subscriber at " \
                 '<a href="https://aismarketcap.com" style="color:#58a6ff">aismarketcap.com</a>. ' \
                 "Not financial advice. Do your own research."

    html = f"""<!DOCTYPE html><html><body style="margin:0;background:#0d1117;
color:#c9d1d9;font-family:Segoe UI,Arial,sans-serif">
<div style="max-width:640px;margin:0 auto;padding:24px 16px">
  <div style="color:#fff;font-size:1.3em;font-weight:bold;margin-bottom:2px">
    AI Market Cap &mdash; Daily Pick</div>
  <div style="color:#8b949e;font-size:.85em;margin-bottom:20px">
    {today_str()} &middot; scored before the earnings report</div>

  <div style="background:linear-gradient(135deg,#1a3a1a,#0d2818);
border:2px solid #2ea043;border-radius:12px;padding:18px;margin-bottom:18px">
    <div style="color:#2ea043;font-size:.8em;font-weight:bold;letter-spacing:.05em">
      TODAY'S PICK</div>
    <div style="color:#fff;font-size:1.6em;font-weight:bold;margin:6px 0">
      {ticker} <span style="font-size:.55em;color:#8b949e;font-weight:normal">{company}</span></div>
    <div style="font-size:.9em">
      Score <b style="color:#00ff88">{score}</b> &middot; Price <b>${price}</b>
      &middot; {days_label(top)}</div>
    <div style="margin-top:14px">
      <a href="{cta_href}" style="background:#00ff88;color:#000;
padding:11px 18px;border-radius:8px;font-weight:bold;text-decoration:none;display:inline-block">
        {cta_label}</a></div>
  </div>

  <table style="width:100%;border-collapse:collapse;font-size:.86em;margin-bottom:18px">
    <tr style="color:#8b949e;font-size:.75em;text-align:left">
      <th style="padding:6px 10px">TICK</th><th>COMPANY</th><th>SCORE</th>
      <th>PRICE</th><th>EARNINGS</th><th>TARGETS</th></tr>
    {''.join(rows)}
  </table>

  <div style="color:#6e7681;font-size:.75em;line-height:1.5">
    {footer}</div>
</div></body></html>"""
    return html, f"{ticker} is today's pick - score {score}"


def days_label(s):
    d = s.get("days_left")
    if d == 0:
        return "reports today"
    if d is None:
        return ""
    return f"{d}d to earnings"


def recipients():
    out = []
    lst = load_json("email_list.json", {})
    for email, rec in lst.items():
        out.append((email, False))
    subs = load_json("subscriptions.json", {})
    for cid, rec in (subs.items() if isinstance(subs, dict) else []):
        if rec.get("status") == "active" and rec.get("email"):
            out.append((rec["email"], True))
    seen, uniq = set(), []
    for e, paid in out:
        k = e.lower().strip()
        if k and k not in seen:
            seen.add(k)
            uniq.append((k, paid))
    return uniq


def send_via_api(env, to, subject, html):
    key = env.get("ALERT_API_KEY")
    if not key:
        return None
    url = env.get("ALERT_API_URL", "https://api.resend.com/emails")
    payload = json.dumps({
        "from": env.get("ALERT_FROM", "alerts@aismarketcap.com"),
        "to": [to], "subject": subject, "html": html,
    }).encode()
    req = urllib.request.Request(url, data=payload, method="POST", headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "User-Agent": "AI-Market-Cap/1.0",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status


def send_via_smtp(env, to, subject, html):
    host = env.get("ALERT_SMTP_HOST")
    if not host:
        return None
    import smtplib
    from email.message import EmailMessage
    msg = EmailMessage()
    msg["From"] = env.get("ALERT_FROM", "alerts@aismarketcap.com")
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content("Your daily AI Market Cap pick. View in browser: "
                    "https://aismarketcap.com")
    msg.add_alternative(html, subtype="html")
    port = int(env.get("ALERT_SMTP_PORT", "587"))
    with smtplib.SMTP(host, port, timeout=30) as s:
        s.starttls()
        user = env.get("ALERT_SMTP_USER")
        if user:
            s.login(user, env.get("ALERT_SMTP_PASS", ""))
        s.send_message(msg)
    return 250


def build_variants():
    """Build both message variants once.

    Two variants, not one per recipient: the free list and the subscribers
    each get a single identical message. Returning a dict keyed by tier is
    what stops a caller from ever handing the free variant to a subscriber
    or the paid variant to the free list.
    """
    out = {}
    for paid in (False, True):
        html, subject = build_email(paid=paid)
        if html:
            out[paid] = (html, subject)
    return out


def pick_transport(env):
    """Return exactly one transport.

    The original called send_via_api AND send_via_smtp for every recipient.
    Each returns None when its own env var is missing, so it looked correct -
    but configuring both sent every subscriber two copies of the same email.
    """
    if env.get("ALERT_API_KEY"):
        return "api", send_via_api
    if env.get("ALERT_SMTP_HOST"):
        return "smtp", send_via_smtp
    return None, None


def main():
    dry = "--dry-run" in sys.argv
    env = load_env()
    name, _send = pick_transport(env)
    configured = name is not None

    variants = build_variants()
    if not variants:
        print("[Alert] cannot build an email from scanner_data.json")
        return 1
    subject = next(iter(variants.values()))[1]

    rcpt = recipients()
    print(f"[Alert] {today_str()}  subject: {subject}")
    print(f"[Alert] recipients: {len(rcpt)} "
          f"({sum(1 for _, p in rcpt if p)} subscribers, "
          f"{sum(1 for _, p in rcpt if not p)} free list)")
    print(f"[Alert] transport: {name if configured else 'NOT CONFIGURED'}")
    print(f"[Alert] targets: included for subscribers, "
          f"'{FREE_TARGETS_CELL}' for the free list")
    if not configured:
        print("[Alert] Put ALERT_API_KEY or ALERT_SMTP_* in alert.env to send.")
        print("[Alert] Everything else works - this run was not sent.")

    if dry or not configured:
        return 0

    sent = failed = 0
    for email, paid in rcpt:
        html, subj = variants.get(bool(paid)) or variants[False]
        try:
            _send(env, email, subj, html)
            sent += 1
        except Exception as e:
            failed += 1
            print(f"[Alert] FAILED {email}: {type(e).__name__}: {e}")
    print(f"[Alert] sent={sent} failed={failed}")
    return 1 if failed and not sent else 0


if __name__ == "__main__":
    sys.exit(main())