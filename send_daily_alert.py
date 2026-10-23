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

import email_unsubscribe as _eu

SITE = Path(__file__).parent
# Which addresses already received today's alert. Written locally, never
# committed - it holds subscriber email addresses.
SENT_LOG = SITE / "alert_sent_log.json"
# A PREDICATE with no addresses and no secrets, which the daily scan commits
# so the deployed site can report honestly. /api/alert-status runs on Railway
# and therefore can never see alert.env or the local log - the sender runs on
# Tyler's machine. Asking the deployed host whether a LOCAL credential exists
# is structurally incapable of a true answer; it would have reported false
# forever even with a working, verified, sending pipeline.
STATUS_FILE = SITE / "alert_status.json"
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
    #
    # BOTH tiers get a CAN-SPAM one-click unsubscribe. The free list is
    # non-payers on the same Resend domain as the paid Pro alert, so a spam
    # event on the free list takes paying customers' mail down with it. There
    # is no "subscribers are exempt" carve-out that a mail provider honours.
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

    # Rendered per recipient at send time, because the token identifies WHO
    # is unsubscribing. A placeholder rather than per-recipient bodies keeps
    # the tier-keyed variant structure that stops the paid message reaching
    # the free list - two safety properties that would otherwise fight.
    unsub_block = (
        '<div style="margin-top:14px;padding-top:12px;'
        'border-top:1px solid #21262d;font-size:.72em;color:#6e7681">'
        'You are receiving this because you asked for the daily pick. '
        '<a href="{{UNSUB_LINK}}" style="color:#58a6ff">Unsubscribe</a>'
        '</div>')

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
  {unsub_block}
</div></body></html>"""
    return html, f"{ticker} is today's pick - score {score}"


UNSUB_PLACEHOLDER = "{{UNSUB_LINK}}"
_UNSUB_WARNED = {"done": False}


def unsubscribe_url(email, env):
    """Per-recipient one-click link, or the site fallback if unconfigured.

    The fallback is a real warning path, not a silent one. Without
    EMAIL_EXPORT_TOKEN there is no way to sign an address-specific link, but
    refusing to send would take the PAID alert down with it - and the paid
    alert is the thing customers pay for. So the message goes out with a
    visible link to the site and this says so out loud, once per run.
    """
    link = _eu.unsubscribe_link(email, env.get("EMAIL_EXPORT_TOKEN"))
    if link:
        return link
    if not _UNSUB_WARNED["done"]:
        _UNSUB_WARNED["done"] = True
        print("[Alert] WARN - EMAIL_EXPORT_TOKEN is not set, so no signed "
              "one-click link can be built.")
        print("[Alert]         Messages will carry a site link instead. "
              "Until that variable exists on")
        print("[Alert]         Railway the unsubscribe is NOT compliant, and "
              "the free list cannot be pulled.")
    return "https://aismarketcap.com"


def render_unsub(html, email, env):
    """Substitute the per-recipient unsubscribe link.

    Raises if the placeholder somehow survived: an email going out with a
    literal {{UNSUB_LINK}} in the footer is worse than no footer at all,
    because it looks delivered.
    """
    out = html.replace(UNSUB_PLACEHOLDER, unsubscribe_url(email, env))
    if UNSUB_PLACEHOLDER in out:
        raise ValueError("unsub placeholder survived substitution")
    return out


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
    # An explicit one-click unsubscribe suppresses the daily email for
    # EVERYONE, subscriber or not. It is stored in email_list.json because
    # that is where the unsubscribe route writes it, so it has to be
    # consulted for paid addresses too - a paying customer who opts out of
    # the email must actually stop receiving mail, not just the free list.
    # Cancelling the PAID plan is a separate action and stays with Stripe.
    #
    # Absence from the list is NOT an unsubscribe. The container holding
    # these records is destroyed on every deploy, so a missing address means
    # "signed up before the last restart", which is the normal state.
    suppressed = {e.lower().strip() for e, r in lst.items()
                  if isinstance(r, dict) and r.get("unsubscribed")}

    for email, rec in lst.items():
        if email.lower().strip() in suppressed:
            continue
        out.append((email, False))
    subs = load_json("subscriptions.json", {})
    for cid, rec in (subs.items() if isinstance(subs, dict) else []):
        if rec.get("status") == "active" and rec.get("email"):
            e = rec["email"]
            if e.lower().strip() in suppressed:
                continue
            out.append((e, True))
    # TIER PRECEDENCE - the paid tier WINS a collision, deliberately.
    #
    # The free list is appended first (above) and paid second, so a plain
    # first-wins dedup silently gives the LEAST valuable tier the address.
    # A customer who pays $5/month AND happens to have signed up free before
    # subscribing would then be sent the FREE email: no entry, no targets, no
    # stop - exactly the thing they are paying for, downgraded with nothing
    # anywhere reporting it, because the run log counts them under the free
    # list and a successful run looks completely normal.
    #
    # Both tiers can legitimately contain the same address, so the collision
    # is a NORMAL state to handle, not an edge case to assume away. Note the
    # key is the normalised address, so the free list's raw casing and padding
    # do not let a paid subscriber slip through the collision.
    #
    # Do not "simplify" this back to first-wins. It looks like a style choice
    # and is the difference between serving and silently not serving a payer.
    seen = {}
    for e, paid in out:
        k = e.lower().strip()
        if not k:
            continue
        if k not in seen or paid:
            seen[k] = (k, paid)
    return list(seen.values())


def list_stats():
    """Counts for the status file, so the channel cannot look healthy
    while it is actually switched off.

    free_list_total is addresses ever captured; free_list_active excludes
    unsubscribes. A free page advertising signup while active is zero is the
    exact failure this whole lane existed to fix, so it is published rather
    than inferred from a total that only ever counted the paying customer.
    """
    lst = load_json("email_list.json", {})
    total = len(lst)
    dead = sum(1 for r in lst.values()
               if isinstance(r, dict) and r.get("unsubscribed"))
    return total, total - dead, dead


def send_via_api(env, to, subject, html, unsub_url=None):
    key = env.get("ALERT_API_KEY")
    if not key:
        return None
    url = env.get("ALERT_API_URL", "https://api.resend.com/emails")
    payload = json.dumps({
        "from": env.get("ALERT_FROM", "alerts@aismarketcap.com"),
        "to": [to], "subject": subject, "html": html,
    }).encode()
    hdrs = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "User-Agent": "AI-Market-Cap/1.0",
    }
    # List-Unsubscribe-Post is what makes it ONE-CLICK: Gmail and Apple Mail
    # POST to this URL directly and never show the user the page. Without the
    # pair, the header is decorative and the recipient still has to find it.
    # Both tiers get it - the free list is non-payers on the same domain as
    # the paid alert, and a spam event on one takes the other down.
    if unsub_url:
        hdrs["List-Unsubscribe"] = "<%s>" % unsub_url
        hdrs["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
    req = urllib.request.Request(url, data=payload, method="POST", headers=hdrs)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status


def send_via_smtp(env, to, subject, html, unsub_url=None):
    host = env.get("ALERT_SMTP_HOST")
    if not host:
        return None
    import smtplib
    from email.message import EmailMessage
    msg = EmailMessage()
    msg["From"] = env.get("ALERT_FROM", "alerts@aismarketcap.com")
    msg["To"] = to
    msg["Subject"] = subject
    if unsub_url:
        msg["List-Unsubscribe"] = "<%s>" % unsub_url
        msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
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


def load_sent_log():
    try:
        return json.loads(SENT_LOG.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_status(name, sent, failed, total, ok):
    """Publish a secret-free, address-free record of what just happened.

    The free-list counts are in here for a specific reason. "recipients: 1,
    sent: 1, failed: 0, last_ok: true" is what a healthy PAID alert looks
    like AND what a completely dead free acquisition channel looked like for
    months. Both rendered as a green total. free_list_active is the number
    that tells those two apart, so it is published rather than inferred.
    """
    try:
        free_total, free_active, free_dead = list_stats()
        payload = {
            "last_run": datetime.now().isoformat(timespec="seconds"),
            "last_ok": bool(ok),
            "sent": sent,
            "failed": failed,
            "recipients": total,
            "transport": name,
            "free_list_total": free_total,
            "free_list_active": free_active,
            "free_list_unsubscribed": free_dead,
        }
        STATUS_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"[Alert] could not write status: {e}")


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
    """Return exactly one transport, or (None, None) if genuinely unusable.

    The original called send_via_api AND send_via_smtp for every recipient.
    Each returns None when its own env var is missing, so it looked correct -
    but configuring both sent every subscriber two copies of the same email.

    A credential is only usable when it is COMPLETE. Testing for
    ALERT_SMTP_HOST alone reported "transport: smtp" against an alert.env
    whose ALERT_SMTP_PASS was still blank, and a --dry-run then announced a
    transport it could not authenticate with. This mirrors the rule
    /api/alert-status applies, so the sender, the endpoint and the guards
    cannot disagree about whether alerts are deliverable.
    """
    if (env.get("ALERT_API_KEY") or "").strip():
        return "api", send_via_api
    host = (env.get("ALERT_SMTP_HOST") or "").strip()
    user = (env.get("ALERT_SMTP_USER") or "").strip()
    pw = (env.get("ALERT_SMTP_PASS") or "").strip()
    if host and user and pw:
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
        if dry:
            # A dry run must never be mistakable for a send. Previously it
            # exited quietly once a credential existed, which is the exact
            # "silent no-op" the growth guard exists to forbid.
            print(f"[Alert] DRY RUN - nothing was sent to {len(rcpt)} recipient(s)")
        return 0

    # Idempotency. The scan runs twice daily and exits non-zero on any
    # failure, so the 13:00 retry must not mail anyone the 06:31 run already
    # reached. The previous code exited 0 on a PARTIAL failure: one bad
    # address marked the whole day as sent and was never retried at all,
    # while a successful retry would have duplicated everyone else.
    log = load_sent_log()
    already = set()
    if log.get("date") == today_str():
        already = {a.lower() for a in (log.get("sent_to") or [])}
    if already:
        print(f"[Alert] {len(already)} recipient(s) already received today's alert")

    sent = failed = 0
    sent_to, failed_to = [], []
    for email, paid in rcpt:
        if email.lower() in already:
            sent += 1
            sent_to.append(email)
            continue
        html, subj = variants.get(bool(paid)) or variants[False]
        try:
            # Render per recipient here, not in build_variants(), so the
            # variant map stays keyed by tier and can never hand the paid
            # body to the free list.
            link = unsubscribe_url(email, env)
            _send(env, email, subj, render_unsub(html, email, env), link)
            sent += 1
            sent_to.append(email)
        except Exception as e:
            failed += 1
            failed_to.append(email)
            print(f"[Alert] FAILED {email}: {type(e).__name__}: {e}")
    print(f"[Alert] sent={sent} failed={failed}")

    try:
        SENT_LOG.write_text(json.dumps({
            "date": today_str(),
            "at": datetime.now().isoformat(timespec="seconds"),
            "sent_to": sent_to,
            "failed_to": failed_to,
        }, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"[Alert] could not write sent-log: {e}")

    write_status(name, sent, failed, len(rcpt), ok=(failed == 0))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())