#!/usr/bin/env python3
"""Pull the free-signup list off Railway into the local email_list.json.

WHY THIS EXISTS
Free-page signups are captured by scanner_web.py, which runs inside Railway's
container. That container's disk is destroyed on every deploy. The sender,
send_daily_alert.py, runs on Tyler's machine and reads a LOCAL copy. Until
this existed the two never met: the site answered "Check your inbox tomorrow
morning" to every signup and then lost it.

THE MERGE RULE THAT MATTERS MOST
A missing address on the remote does NOT mean unsubscribed. It means the
container was replaced since that address signed up, which is the normal
state of an ephemeral disk. Overwriting the local list with the remote one -
or deleting local entries the remote happens not to have - would therefore
silently unsubscribe people on the next deploy.

Only an explicit "unsubscribed" flag, set by the one-click unsubscribe route,
removes anybody. Anything else only ever adds or refreshes.

HONESTY
Three outcomes must never look alike:
  * 403 / no token  -> the channel is NOT configured. This is a warning.
  * 200 with count 0 -> genuinely zero signups. This is a fact.
  * 200 with count N -> N signups.
Collapsing the first into the second is exactly how this bug would have
looked healthy for another month.

Run:  python pull_email_list.py [--dry-run]
Exit 0 = list is current. Exit 1 = not configured, or the pull failed loudly.
"""
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

SITE = Path(__file__).parent
LIST_FILE = SITE / "email_list.json"
ENV_FILE = SITE / "alert.env"
SITE_URL = os.environ.get("SITE_URL", "https://aismarketcap.com")
EXPORT_URL = SITE_URL.rstrip("/") + "/api/email-list-export"
PT_TZ = None
try:
    from zoneinfo import ZoneInfo
    PT_TZ = ZoneInfo("America/Los_Angeles")
except Exception:
    pass


def now_iso():
    return datetime.now(PT_TZ).isoformat(timespec="seconds") if PT_TZ \
        else datetime.now().isoformat(timespec="seconds")


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


def fetch(env, timeout=30):
    """Return (list, None) or (None, reason). Never prints an address.

    CLOUDFLARE SITS IN FRONT OF THIS AND THE DIFFERENCE MATTERS
    Cloudflare error 1010 ("browser integrity check") refuses any request
    whose User-Agent does not look like a browser. Python's default
    Python-urllib/3.x is refused - on EVERY path, including the homepage. The
    response is an HTML page with the text "error code: 1010", served with
    HTTP 403.

    That is indistinguishable from a 403 by status code alone, and treating
    them the same is how you get a confident wrong diagnosis. A previous
    probe concluded "the secret is rejected" from a 403 that Cloudflare had
    produced before the app ever saw the request - the same class of error
    as reading a cached file and calling it the source of truth.

    So this distinguishes them explicitly. It does NOT try to slip past the
    check with a spoofed browser User-Agent: that control exists to stop
    exactly that, and evading it would be both fragile and dishonest. The
    real fix belongs in Cloudflare - skip the browser-integrity check for
    /api/* or allow this client - and only Tyler can set that.
    """
    token = (env.get("EMAIL_EXPORT_TOKEN") or "").strip()
    if not token:
        return None, "EMAIL_EXPORT_TOKEN is not set in alert.env"
    req = urllib.request.Request(EXPORT_URL, method="GET", headers={
        "X-Email-Token": token,
        "User-Agent": "AI-Market-Cap-EmailPull/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            payload = json.loads(r.read().decode("utf-8", "ignore"))
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", "ignore")
        except Exception:
            pass
        if "1010" in body:
            return None, (
                "Cloudflare blocked this client BEFORE it reached the app "
                "(browser integrity check, error 1010). This is NOT a token "
                "problem and no amount of re-pasting the token will change "
                "it. Cloudflare must skip that check for /api/* - only Tyler "
                "can set that.")
        if e.code == 403:
            return None, ("the app returned 403 - EMAIL_EXPORT_TOKEN is not "
                          "set on Railway, or does not match alert.env")
        return None, "HTTP %s from the export endpoint" % e.code
    except Exception as e:
        return None, "%s: %s" % (type(e).__name__, e)
    if not isinstance(payload, dict) or "list" not in payload:
        return None, "export returned an unexpected shape"
    return payload.get("list") or {}, None


def merge(local, remote):
    """Fold remote into local. Never deletes. Returns counters."""
    added = refreshed = unsubscribed = 0
    out = dict(local)
    for email, rec in remote.items():
        email = str(email).strip().lower()
        if not email:
            continue
        rec = rec if isinstance(rec, dict) else {}
        prev = out.get(email)
        if prev is None:
            out[email] = dict(rec)
            out[email].setdefault("added", now_iso())
            out[email].setdefault("last_seen", now_iso())
            out[email].setdefault("seen_count", 1)
            out[email]["pulled_from"] = "railway"
            added += 1
            continue
        merged = dict(prev)
        for field in ("added", "source"):
            if rec.get(field):
                merged.setdefault(field, rec[field])
        merged["last_seen"] = rec.get("last_seen") or prev.get("last_seen")
        try:
            merged["seen_count"] = max(int(prev.get("seen_count", 1) or 1),
                                      int(rec.get("seen_count", 1) or 1))
        except Exception:
            merged["seen_count"] = prev.get("seen_count", 1)
        if rec.get("unsubscribed"):
            merged["unsubscribed"] = rec["unsubscribed"]
            if not prev.get("unsubscribed"):
                unsubscribed += 1
        elif prev.get("unsubscribed"):
            # The remote container lost this record, but the local copy knows
            # the person opted out. A deploy must not undo an unsubscribe.
            merged["unsubscribed"] = prev["unsubscribed"]
        merged["pulled_from"] = "railway"
        out[email] = merged
        refreshed += 1
    return out, added, refreshed, unsubscribed


def main():
    dry = "--dry-run" in sys.argv
    env = load_env()

    remote, err = fetch(env)
    if err:
        print("[EmailPull] NOT PULLED - %s" % err)
        print("[EmailPull] Free signups are being captured but cannot reach "
              "this machine. Nothing was changed.")
        return 1

    local = {}
    if LIST_FILE.exists():
        try:
            local = json.loads(LIST_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            print("[EmailPull] local email_list.json is unreadable (%s); "
                  "starting from empty rather than overwriting blind" % e)

    merged, added, refreshed, unsubs = merge(local, remote)

    active = sum(1 for r in merged.values() if not r.get("unsubscribed"))
    dead = len(merged) - active

    print("[EmailPull] remote=%d local_before=%d  +%d new  ~%d refreshed  "
          "%d newly unsubscribed" % (len(remote), len(local), added,
                                     refreshed, unsubs))
    print("[EmailPull] list now: %d address(es), %d active, %d unsubscribed"
          % (len(merged), active, dead))
    if not remote:
        print("[EmailPull] The channel is WORKING and has zero signups. That "
              "is a fact about the funnel, not a fault.")

    if dry:
        print("[EmailPull] DRY RUN - local file not written")
        return 0

    try:
        LIST_FILE.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    except Exception as e:
        print("[EmailPull] could not write the local list: %s" % e)
        return 1
    print("[EmailPull] written to %s (gitignored, never committed)"
          % LIST_FILE.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())