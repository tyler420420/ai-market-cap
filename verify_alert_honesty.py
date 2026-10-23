r"""/api/alert-status must not be able to report green while sending nothing.

THE TWO FALSE-GREEN STATES
---------------------------
1. Partial credential. The original check matched `ALERT_SMTP_HOST=\S`. That
   line is present in a file whose `ALERT_SMTP_PASS=` is still BLANK - the
   exact state Tyler was in - so the endpoint reported "configured" and every
   send would have failed at authentication.

2. No runner. `send_daily_alert.py` shipped with no caller anywhere: no cron,
   no Railway service, no scheduled task, no hook. Even a perfect credential
   would have produced no mail, ever. A status that reports success while
   delivering nothing is worse than no status, because it ends the question.

So this drives the real view function against real credential states, and
asserts daily_scan.ps1 - the scheduled, unattended writer - invokes the
sender once per day and treats a mail failure as non-fatal, because a mail
outage must never be allowed to abort the scan.

Extraction uses ast, not brace counting: the view contains an f-string, and
counting braces by hand stops in the middle of `{e}`.
"""
import ast
import json
import os
import re
import sys
import tempfile
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
    """Return (source_of_view, needs_path) for api_alert_status."""
    src = web_path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "api_alert_status":
            return ast.get_source_segment(src, node), src
    raise AssertionError("api_alert_status not found in %s" % web_path)


VIEW_SRC, WEB_SRC = extract_view(WEB)


def status_with(env_text):
    """Run the real view body against a given alert.env content.

    None simulates the file being absent entirely - which is what Railway
    sees, because alert.env is gitignored and never deployed.
    """
    tmp = None
    if env_text is not None:
        tmp = Path(tempfile.gettempdir()) / "alert_probe_env.txt"
        tmp.write_text(env_text, encoding="utf-8")
    target = tmp if tmp else Path(r"C:\definitely\not\here\alert.env")
    ns = {
        "Path": Path, "re": re, "jsonify": lambda p: _Resp(p),
        "ALERT_ENV_FILE": target, "print": lambda *a, **k: None,
    }
    try:
        exec(compile(VIEW_SRC, "<api_alert_status>", "exec"), ns)
        res = ns["api_alert_status"]()
        return res.get_json()
    finally:
        if tmp and tmp.exists():
            tmp.unlink()


BLANK = ("ALERT_SMTP_HOST=smtp.gmail.com\nALERT_SMTP_PORT=587\n"
         "ALERT_SMTP_USER=a@b.com\nALERT_SMTP_PASS=\nALERT_FROM=a@b.com\n")
COMPLETE = BLANK.replace("ALERT_SMTP_PASS=\n", "ALERT_SMTP_PASS=abcdefghijklmnop\n")
HOST_ONLY = "ALERT_SMTP_HOST=smtp.gmail.com\n"

# --- 1. the three states that all used to report green ----------------------
d_absent = status_with(None)
check("no credential file at all -> not configured",
      d_absent.get("alerts_configured") is False,
      "endpoint claims configured with no file: %s" % d_absent)

d_host = status_with(HOST_ONLY)
check("host only, no user, no password -> not configured",
      d_host.get("alerts_configured") is False,
      "a bare host line reported ready: %s" % d_host)

d_blank = status_with(BLANK)
check("host + user but BLANK password -> not configured",
      d_blank.get("alerts_configured") is False,
      "half-filled credential reported ready: %s" % d_blank)
check("the blank-password case is specifically rejected by the PASSWORD, not by the host",
      d_blank.get("credential_present") is False,
      "host+user alone satisfied the credential check: %s" % d_blank)

# --- 2. a complete credential ------------------------------------------------
d_full = status_with(COMPLETE)
check("complete credential -> credential_present is true",
      d_full.get("credential_present") is True,
      "a complete credential was rejected: %s" % d_full)
check("a credential alone does NOT flip alerts_configured",
      d_full.get("alerts_configured") is False or d_full.get("runner_wired") is True,
      "alerts_configured ignored the runner: %s" % d_full)
check("alerts_configured is gated on the runner, not just the credential",
      d_full.get("alerts_configured") == bool(d_full.get("runner_wired")),
      "alerts_configured must equal credential AND runner: %s" % d_full)

check("the endpoint leaks no host, user, password or key",
      not any(k in json.dumps(d_full).lower()
              for k in ("smtp.gmail.com", "a@b.com", "abcdefghijklmnop", "alertsmtp")),
      "response leaked credential detail: %s" % d_full)

# --- 3. the runner must actually invoke the sender --------------------------
check("daily_scan.ps1 exists", RUNNER.exists(), "the scheduled runner is missing")
if RUNNER.exists():
    body = RUNNER.read_text(encoding="utf-8", errors="ignore")
    check("daily_scan.ps1 invokes send_daily_alert.py",
          "send_daily_alert.py" in body,
          "nothing in the scheduled runner ever sends the alert")
    check("the alert sends at most once per day",
          ".alert_sent_today.txt" in body,
          "the scan runs twice daily with no once-a-day gate")
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