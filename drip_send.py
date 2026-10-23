#!/usr/bin/env python3
"""Six-email drip to people who signed up for the free pick themselves.

WHAT THIS SENDS TO
Only addresses that arrived through the site's own signup form. NOT the
purchased lead lists, NOT the paid subscriber pool. A free signup is real
consent; a bought Facebook lead is not, and the two are never joined.

STRUCTURAL ISOLATION - read this before "simplifying" it
This module opens exactly ONE data file: drip_queue.json. There is no code
path from here to email_list.json or subscriptions.json. The free-minus-paid
filter happens upstream in drip_queue.py, which writes the queue.

That is deliberate. The paid/free target leak and the first-wins dedup defect
both came from one function being able to see two populations at once. Here
the mistake is not "someone forgot a filter", it is an ImportError.

TWO GATES, BOTH ENFORCED BEFORE ANYTHING IS SENT
  1. A working one-click unsubscribe. CAN-SPAM requires honouring an opt-out
     within 10 business days. Sending a six-email sequence with a dead opt-out
     is not a smaller version of the problem, it is a larger one - a sequence
     generates far more complaints than one daily mail.
  2. A physical postal address in every commercial email. There is none
     configured yet, and no placeholder will be invented to turn this check
     green.

If either is unmet this script sends NOTHING, says which gate failed, and
exits non-zero. A blocked run is the correct outcome, not a failure to route
around. Do not add a --force that skips this.

NO INVENTED NUMBERS
Every figure is read from scanner_data.json at send time. If the scan is
missing or the field is absent, the template omits the sentence. It never
prints a zero, a placeholder, or yesterday's value.

FREE READERS NEVER SEE PRO VALUES
Entry, target and stop are what Pro pays for. This drip goes to non-payers,
so those columns are never rendered - the same PAID_COLUMNS gate the daily
alert uses. Email 3 is carried by ticker, score, days-to-earnings and the
written reasoning instead, which is thinner on purpose.

Run:  python drip_send.py [--dry-run] [--step N]
Exit 0 = sent or dry-run completed. Exit 1 = blocked by a gate, or a send failed.
"""
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path

SITE = Path(__file__).parent
QUEUE = SITE / "drip_queue.json"          # the ONLY list this script reads
SENT_LOG = SITE / "drip_sent_log.json"    # gitignored, holds addresses
STATUS_FILE = SITE / "drip_status.json"   # committed, no addresses
ENV_FILE = SITE / "alert.env"
SITE_URL = os.environ.get("SITE_URL", "https://aismarketcap.com")

PT_TZ = None
try:
    from zoneinfo import ZoneInfo
    PT_TZ = ZoneInfo("America/Los_Angeles")
except Exception:
    pass

# The six. (step, day_offset, subject, intent)
SEQUENCE = [
    (1, 0,  "Your first pick is already live",
     "value only. Never sells - an ask before value gets unsubscribes, "
     "not subscribers."),
    (2, 2,  "How we score a pre-earnings setup",
     "the five scoring factors, explained"),
    (3, 4,  "Today's pick, and the reasoning",
     "worked example from real scanner output"),
    (4, 6,  "What Pro adds: entry, target, stop-loss",
     "first paid mention"),
    (5, 9,  "Tomorrow's earnings on the scanner",
     "recency, pull back to the site"),
    (6, 12, "Last note from me",
     "sunset, then stop"),
]

# Pro-only. Never rendered for a free drip recipient.
PAID_COLUMNS = ("pe_target", "3d", "5d")


def now():
    return datetime.now(PT_TZ) if PT_TZ else datetime.now()


def today_str():
    return now().strftime("%Y-%m-%d")


def load_env():
    env = dict(os.environ)
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8",
                                       errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


# ---------------------------------------------------------------- gates ----

def gate_optout(env):
    """A one-click unsubscribe that actually works.

    Existence of the token is not proof. The token can be set here and absent
    on Railway, and then every opt-out a recipient clicks returns 503 and
    nothing is suppressed - which is the violation the gate exists to stop.

    So this probes the live route with a deliberately INVALID token and reads
    the distinction:
        503 not_configured -> the service has no token. Not safe to send.
        400 bad_token       -> the service is configured and validating.
                               Nothing real was touched; 'invalid.invalid'
                               cannot be anyone's address.
    The probe is a no-op on real data by construction.
    """
    if not (env.get("EMAIL_EXPORT_TOKEN") or "").strip():
        return False, "EMAIL_EXPORT_TOKEN is not set locally"
    url = SITE_URL.rstrip("/") + "/api/email-unsubscribe?t=invalid.invalid"
    req = urllib.request.Request(
        url, method="POST", data=b"List-Unsubscribe=One-Click",
        headers={"User-Agent": "AI-Market-Cap-Drip/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return False, ("unsubscribe route answered %s - expected 400 for "
                           "an invalid token" % r.status)
    except urllib.error.HTTPError as e:
        if e.code == 400:
            return True, "live route is configured and validating"
        if e.code == 503:
            return False, ("the live site has no EMAIL_EXPORT_TOKEN, so every "
                           "opt-out a recipient clicks would return 503 and "
                           "suppress nothing")
        return False, "unsubscribe route returned unexpected %s" % e.code
    except Exception as e:
        return False, "could not reach the unsubscribe route: %s" % e


def gate_postal(env):
    """A real, deliverable postal address in every commercial email.

    No placeholder. A fake address in a compliance field is worse than an
    absent one: it turns the check green and leaves the actual exposure
    exactly where it was.
    """
    addr = (env.get("POSTAL_ADDRESS") or "").strip()
    if not addr:
        return False, ("no postal address configured - add POSTAL_ADDRESS to "
                       "alert.env. Not substituting a placeholder.")
    if len(addr) < 10 or "," not in addr:
        return False, ("POSTAL_ADDRESS does not look like a deliverable "
                       "street address: %r" % addr[:40])
    return True, addr


def check_gates(env):
    gates, failures = {}, []
    ok, why = gate_optout(env)
    gates["optout_working"] = {"ok": ok, "detail": why}
    if not ok:
        failures.append("opt-out: " + why)
    ok, why = gate_postal(env)
    gates["postal_address"] = {"ok": ok, "detail": why}
    if not ok:
        failures.append("postal: " + why)
    return gates, failures


def write_status(payload):
    try:
        STATUS_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception as e:
        print("[Drip] could not write status: %s" % e)


# -------------------------------------------------------------- rendering --

def money(v):
    try:
        return "${:,.2f}".format(float(v))
    except Exception:
        return None


def top_picks():
    """Real scanner output, or []. Never a fallback number."""
    try:
        data = json.loads((SITE / "scanner_data.json").read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(data, list):
        return []
    return [s for s in data if isinstance(s, dict)
            and (s.get("score") or 0) >= 75][:5]


def days_label(s):
    d = s.get("days_left")
    if d == 0:
        return "reports today"
    if d is None:
        return ""
    return "%dd to earnings" % d


def body_for(step, env):
    """Render one email. Returns (html, subject) or (None, reason)."""
    picks = top_picks()
    top = picks[0] if picks else None
    subj = next(s[2] for s in SEQUENCE if s[0] == step)

    head = ('<div style="color:#fff;font-size:1.25em;font-weight:bold">'
            'AI Market Cap</div>'
            '<div style="color:#8b949e;font-size:.82em;margin-bottom:18px">'
            'The free daily pick &middot; %s</div>' % today_str())

    if step == 1:
        # Value only. No ask, no mention of price anywhere in this one.
        p = ('Your first pick is already live. Open the scanner and the '
             "top-ranked setup is at the top of the table, scored before the "
             'earnings report, with the date it reports.') if top else (
            'Your first pick is already live. Open the scanner and the '
            'top-ranked setup is at the top of the table.')
        inner = p
    elif step == 2:
        inner = ("We rank every pre-earnings setup on five factors: analyst "
                 "coverage, share-buyback conviction, the size and strength "
                 "of the buy signal, the five-day price setup, and earnings "
                 "sentiment. The score is 0 to 100 and it is the same score "
                 "you see in the table &mdash; not a marketing number.")
    elif step == 3:
        # NO entry, target or stop. Those are Pro values and this is a free
        # reader. Carried by ticker, score, timing and reasoning only.
        if not top:
            return None, "no scanner data above the threshold; skipping #3"
        ticker = top.get("ticker", "?")
        comp = top.get("company_name", "")
        score = top.get("score", "?")
        when = days_label(top) or "ahead of its report"
        inner = ("Today&rsquo;s top setup is <b>%s</b>%s at score %s, %s. "
                 "Read the full table for the rest, and the reasoning behind "
                 "each rank is in the row itself."
                 % (ticker,
                    (" &middot; " + comp) if comp else "",
                    score, when))
    elif step == 4:
        inner = ("Pro adds three numbers to every setup: the entry price, the "
                 "3, 7 and 14-day targets, and the stop-loss. Everything in "
                 "the free table stays free either way.")
    elif step == 5:
        inner = ("The scanner runs before the open and ranks what reports "
                 "soonest against the strongest setup, so tomorrow&rsquo;s "
                 "list is ready when you wake up.")
    else:
        inner = ("That is the last note in this sequence. The scanner stays "
                 "free and open at aismarketcap.com, and you will not hear "
                 "from this address again.")

    footer = ('<div style="color:#6e7681;font-size:.72em;line-height:1.6;'
              'margin-top:22px;padding-top:12px;border-top:1px solid #21262d">'
              'AI Market Cap &middot; %s<br>'
              '<a href="{{UNSUB}}" style="color:#58a6ff">Unsubscribe</a>'
              '</div>' % env["POSTAL_ADDRESS"].strip())

    html = ("<!DOCTYPE html><html><body style=\"margin:0;background:#0d1117;"
            "color:#c9d1d9;font-family:Segoe UI,Arial,sans-serif\">"
            "<div style=\"max-width:600px;margin:0 auto;padding:24px 16px\">"
            + head + "<p style=\"line-height:1.65;font-size:.95em\">"
            + inner + "</p>"
            '<div style="margin-top:16px"><a href="' + SITE_URL + '" '
            'style="background:#00ff88;color:#000;padding:10px 16px;'
            'border-radius:8px;font-weight:bold;text-decoration:none;'
            'display:inline-block">Open the scanner</a></div>'
            + footer + "</div></body></html>")
    return html, subj


# ------------------------------------------------------------------ send ---

def refresh_inputs():
    """Re-derive the queue immediately before selecting recipients.

    A queue built once per cycle is wrong twice over. A free reader who
    subscribes to Pro two hours later is still in it, so tomorrow they get
    email 4 - "What Pro adds: entry, target, stop-loss" - from the company
    they just paid. That is the paid/free leak arriving a day late and
    looking worse, not better.

    And an unsubscribe that lands between build and send must still win.

    So the paid set is re-read from Stripe live first (reconcile_subscriptions
    asks Stripe what is actually active, rather than trusting a file that may
    be a day old), then the queue is rebuilt. Both steps are NON-FATAL: if
    either fails we say so and continue on the last known data, because a
    stale exclusion is bad but refusing to send over it is worse. The reason
    is logged either way so it is never silent.
    """
    import subprocess
    notes = []
    recon = SITE / "reconcile_subscriptions.py"
    if recon.exists():
        p = subprocess.run([sys.executable, "-X", "utf8", str(recon)],
                           capture_output=True, text=True, cwd=str(SITE))
        if p.returncode != 0:
            notes.append("paid set may be stale: reconcile exited %s" % p.returncode)
    builder = SITE / "drip_queue.py"
    p = subprocess.run([sys.executable, "-X", "utf8", str(builder)],
                       capture_output=True, text=True, cwd=str(SITE))
    if p.returncode != 0:
        notes.append("queue rebuild exited %s: %s"
                     % (p.returncode, (p.stdout or "")[-160:]))
    return notes


def load_queue():
    try:
        return json.loads(QUEUE.read_text(encoding="utf-8"))
    except Exception:
        return None


def recipients_due(queue):
    """Which (email, step) pairs are due now. Idempotent by construction.

    An address already sent a step never gets it again, so a resumed or
    duplicated run cannot re-send email #1 - the classic drip bug, and one
    that is invisible until a recipient complains.

    Reads the queue and the local sent log. Nothing else.
    """
    log = {}
    try:
        log = json.loads(SENT_LOG.read_text(encoding="utf-8"))
    except Exception:
        pass
    due, sent_map = [], {}
    for rec in queue if isinstance(queue, list) else []:
        if not isinstance(rec, dict):
            continue
        email = (rec.get("email") or "").strip().lower()
        if not email or rec.get("unsubscribed"):
            continue
        seen = set((log.get(email) or {}).get("steps") or [])
        sent_map[email] = sorted(seen)
        pending = [s for s, _o, _su, _i in SEQUENCE if s not in seen]
        if not pending:
            continue
        day0 = rec.get("day0")
        if day0:
            try:
                ready = (datetime.strptime(day0, "%Y-%m-%d") + timedelta(
                    days=dict((s, o) for s, o, _su, _i in SEQUENCE)[pending[0]])
                    ).date() <= now().date()
            except Exception:
                ready = True
        else:
            ready = True
        if ready:
            due.append((email, pending[0]))
    return due, sent_map, log


def send(env, to, subject, html, unsub_url):
    import email_unsubscribe as eu
    payload = json.dumps({
        "from": env.get("ALERT_FROM", "alerts@aismarketcap.com"),
        "to": [to], "subject": subject, "html": html,
    }).encode()
    hdrs = {"Authorization": "Bearer " + env["ALERT_API_KEY"],
            "Content-Type": "application/json",
            "User-Agent": "AI-Market-Cap-Drip/1.0"}
    if unsub_url:
        hdrs["List-Unsubscribe"] = "<%s>" % unsub_url
        hdrs["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
    req = urllib.request.Request(env["ALERT_API_URL"], data=payload,
                                 method="POST", headers=hdrs)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status


def main():
    dry = "--dry-run" in sys.argv
    env = load_env()
    gates, failures = check_gates(env)

    if failures:
        print("[Drip] BLOCKED - sending nothing. %d gate(s) unmet:" % len(failures))
        for f in failures:
            print("[Drip]   - " + f)
        write_status({
            "last_run": now().isoformat(timespec="seconds"),
            "last_ok": False, "blocked": True, "sent": 0,
            "gates": gates, "reasons": failures,
        })
        return 1

    if not (env.get("ALERT_API_KEY") or "").strip():
        print("[Drip] BLOCKED - ALERT_API_KEY missing")
        return 1

    # Re-derive the paid set and the queue IMMEDIATELY before selecting, not
    # once per cycle. See refresh_inputs() for why a cached queue is wrong.
    stale_notes = refresh_inputs()

    try:
        queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    except Exception as e:
        print("[Drip] no queue: %s" % e)
        write_status({"last_run": now().isoformat(timespec="seconds"),
                      "last_ok": False, "blocked": False, "sent": 0,
                      "gates": gates, "reasons": ["no drip_queue.json"]})
        return 1

    due, already, log = recipients_due(queue)

    print("[Drip] queue=%d  due_now=%d" % (len(queue or []), len(due)))
    print("[Drip] gates passed: opt-out verified live, postal address present")
    for n in stale_notes:
        print("[Drip] WARNING - " + n)

    sent = failed = 0
    for email, step in due:
        html, subj = body_for(step, env)
        if html is None:
            print("[Drip] skip %s step %d: %s" % (email, step, subj))
            continue
        link = None
        try:
            import email_unsubscribe as eu
            link = eu.unsubscribe_link(email, env.get("EMAIL_EXPORT_TOKEN"))
        except Exception:
            link = None
        if not link:
            print("[Drip] skip %s: could not build an unsubscribe link" % email)
            continue
        html = html.replace("{{UNSUB}}", link)
        if "{{UNSUB}}" in html:
            print("[Drip] skip %s: placeholder survived" % email)
            continue
        try:
            if dry:
                print("[Drip]   [dry] step %d -> %s  %s" % (step, email, subj))
            else:
                send(env, email, subj, html, link)
            sent += 1
            steps = already.get(email, [])
            steps.append(step)
            log[email] = {"steps": sorted(set(steps)), "last": today_str()}
        except Exception as e:
            failed += 1
            print("[Drip] FAILED %s: %s: %s" % (email, type(e).__name__, e))

    if not dry and sent:
        try:
            SENT_LOG.write_text(json.dumps(log, indent=2), encoding="utf-8")
        except Exception as e:
            print("[Drip] could not write sent log: %s" % e)

    write_status({
        "last_run": now().isoformat(timespec="seconds"),
        "last_ok": failed == 0, "blocked": False, "dry_run": dry,
        "sent": sent, "failed": failed,
        "queue_size": len(queue or []),
        "gates": gates,
    })
    print("[Drip] sent=%d failed=%d%s" % (sent, failed, " (dry)" if dry else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())