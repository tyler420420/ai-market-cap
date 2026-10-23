r"""/api/alert-status must report what ACTUALLY HAPPENED, not what it guesses.

THE STRUCTURAL BUG THIS FIXES
-----------------------------
The sender does not run on Railway. It runs on Tyler's machine, from
daily_scan.ps1. /api/alert-status is served BY Railway. alert.env is
gitignored and never deployed, so the deployed host could never see it.

Asking the deployed host "does a local credential file exist?" is therefore
structurally incapable of a true answer. It reported `false` permanently -
through a verified domain, a working key, and real delivered mail - because
it was measuring the wrong machine. That is worse than having no endpoint: it
looked authoritative and was confidently wrong.

So the sender now publishes alert_status.json after every run (when, how many
sent, how many failed, which transport - no addresses, no credentials), the
daily scan commits it, and the endpoint reports THAT.

WHAT THIS ASSERTS
-----------------
1. Nothing delivered -> not configured.
2. A send older than 48h -> not configured (a missed run stays visible).
3. The runner not invoking the sender -> not configured, whatever the record.
4. A PARTIAL failure still counts as delivered. One mistyped address must not
   read as a broken pipeline - but the failure is exposed as `last_failed`
   rather than hidden behind a boolean.
5. No address, key, host or user ever appears in the response.
6. daily_scan.ps1 still invokes the sender, at most once a day, non-fatally.
"""
import ast
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

SITE = Path(r"C:\Users\Tyler_AI\ai-market-cap")
WEB = Path(os.environ.get("WEB_SRC") or (SITE / "scanner_web.py"))
RUNNER = Path(os.environ.get("RUNNER_SRC") or (SITE / "daily_scan.ps1"))

fails = []
ran = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (("  -> " + detail) if detail and not ok else ""))
    ran.append(name)
    if not ok:
        fails.append(name)


class _Resp:
    def __init__(self, payload):
        self.payload = payload

    def get_json(self):
        return self.payload


def extract_view(web_path):
    """Exact source of api_alert_status via ast - the view contains f-strings,
    so counting braces by hand stops in the middle of {e}."""
    src = web_path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "api_alert_status":
            return ast.get_source_segment(src, node)
    raise AssertionError("api_alert_status not found in %s" % web_path)


VIEW_SRC = extract_view(WEB)


def status_with(record, runner_wired=True):
    """Run the real view against a given alert_status.json, and with or
    without daily_scan.ps1 next to it."""
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        if record is not None:
            (td / "alert_status.json").write_text(
                record if isinstance(record, str) else json.dumps(record), encoding="utf-8")
        if runner_wired:
            (td / "daily_scan.ps1").write_text(
                "# calls send_daily_alert.py", encoding="utf-8")
        ns = {"json": json, "Path": Path, "print": lambda *a, **k: None,
              "datetime": datetime, "os": os,
              "jsonify": lambda p: _Resp(p), "timedelta": timedelta}
        exec(compile(VIEW_SRC, "<api_alert_status>", "exec"), ns)
        # The view resolves both files relative to __file__, which ast
        # extraction does not provide, so point it at the temp dir.
        ns["__file__"] = str(td / "scanner_web.py")
        res = ns["api_alert_status"]()
        return res.get_json()


now = datetime.now()
fresh = now - timedelta(hours=2)
old = now - timedelta(days=5)

FRESH = {"last_run": fresh.isoformat(timespec="seconds"), "last_ok": False,
         "sent": 3, "failed": 1, "recipients": 4, "transport": "api"}
OLD = dict(FRESH, last_run=old.isoformat(timespec="seconds"))

# --- nothing has ever been sent ------------------------------------------
d = status_with(None)
check("no delivery record at all -> not configured",
      d.get("alerts_configured") is False, "claimed configured with no record: %s" % d)

# --- an honest recent delivery -------------------------------------------
d = status_with(FRESH)
check("a real send in the last 2h -> alerts_configured is true",
      d.get("alerts_configured") is True, "a delivered alert reported undeliverable: %s" % d)
check("delivered_recently agrees", d.get("delivered_recently") is True, str(d))

# --- a partial failure is not a broken pipeline, and is not hidden -------
check("a partial failure still counts as delivered",
      d.get("alerts_configured") is True,
      "one bad address must not read as a dead pipeline: %s" % d)
check("the failed count is exposed, not hidden",
      d.get("last_failed") == 1 and d.get("last_sent") == 3,
      "the failure vanished: %s" % d)

# --- a stale record goes red ---------------------------------------------
d = status_with(OLD)
check("a send from 5 days ago -> not configured",
      d.get("alerts_configured") is False,
      "a missed run would stay green forever: %s" % d)

# --- the runner still has to invoke the sender ---------------------------
d = status_with(FRESH, runner_wired=False)
check("a fresh send but nothing invokes the sender -> not configured",
      d.get("alerts_configured") is False,
      "a credential-shaped record alone flipped it green: %s" % d)

# --- robustness -----------------------------------------------------------
d = status_with("{ not json")
check("corrupt alert_status.json -> not configured, no exception",
      d.get("alerts_configured") is False, str(d))

d = status_with({"last_run": "not-a-date", "sent": 9, "failed": 0})
check("unparseable timestamp -> not configured",
      d.get("alerts_configured") is False, str(d))

d = status_with({"last_run": fresh.isoformat(timespec="seconds"), "sent": 0, "failed": 2})
check("zero sent -> not configured even though the record exists",
      d.get("alerts_configured") is False, str(d))

# --- nothing sensitive is ever returned -----------------------------------
body = json.dumps(status_with(FRESH)).lower()
check("the response leaks no address, key, host or user",
      not any(k in body for k in ("@", "re_", "smtp.", "password", "api_key")),
      "response leaked detail: %s" % body)

# --- the sender really does publish it -----------------------------------
src = (SITE / "send_daily_alert.py").read_text(encoding="utf-8")
check("the sender writes alert_status.json", "alert_status.json" in src or "STATUS_FILE" in src,
      "nothing publishes the record this endpoint depends on")
check("the sender writes no addresses into the status file",
      "write_status" in src and "sent_to" not in src.split("write_status(")[1][:400],
      "subscriber addresses are being written to a COMMITTED file")

# --- the runner -----------------------------------------------------------
check("daily_scan.ps1 exists", RUNNER.exists())
if RUNNER.exists():
    body = RUNNER.read_text(encoding="utf-8", errors="ignore")
    check("daily_scan.ps1 invokes send_daily_alert.py",
          "send_daily_alert.py" in body)
    check("the alert sends at most once per day", ".alert_sent_today.txt" in body)
    check("the alert skips cleanly when alert.env is absent",
          "alert.env" in body and "SKIP" in body)
    after = body.split("send_daily_alert.py", 1)[-1][:1200]
    check("a mail failure cannot abort the scan",
          "exit 1" not in after,
          "the alert block contains a hard exit inside the scan path")

print()
if fails:
    print("RESULT: %d FAILED -> %s" % (len(fails), ", ".join(fails)))
    sys.exit(1)
print("RESULT: ALL PASS (%d checks)" % len(ran))