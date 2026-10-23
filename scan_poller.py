#!/usr/bin/env python3
"""On-demand scan poller - runs on Tyler's machine, not on Railway.

WHY THIS EXISTS
---------------
Tyler 2026-10-22: "point the scan to my local machine, that is best solution."

The scanner cannot run inside the Railway container: it OOM'd the container into
a restart loop that 404'd every route, which is why ALLOW_IN_CONTAINER_SCAN is
off. The scanner runs perfectly well HERE, where daily_scan.ps1 already scans,
commits and pushes so Railway redeploys the fresh HTML.

So this poller:
  1. asks Railway every POLL_S for a pending on-demand scan
  2. if one is claimed, runs daily_scan.ps1
  3. reports the result back so Railway can show the subscriber

PULL, NOT PUSH. This machine is behind NAT. Exposing a tunnel so Railway could
call in would mean a public endpoint that can start scans - a lever anyone
could pull to burn the account. Instead Railway only ever stores a request and
this machine pulls it with a shared secret.

RUN IT
    setx SCAN_SECRET "<the secret>"          # once, then a new terminal
    python scan_poller.py
Or via the scheduled task scan_poller_task.ps1, which is what runs it 24/7.

SECRET
    Reads SCAN_SECRET from the environment, or from scan.env next to this file
    (gitignored). Both Railway and this machine need the SAME value.
"""
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
SITE = "https://aismarketcap.com"
SCAN_PS1 = HERE / "daily_scan.ps1"
POLL_S = 60                      # ask Railway once a minute
LOG_PATH = HERE / "scan_poller.log"
# daily_scan.ps1 takes ~4 minutes. Generous, because a timeout here would
# release the claim while the scan is still running and a second poller could
# start a duplicate.
SCAN_TIMEOUT_S = 900
LOCK = HERE / "scan_poller.lock"


def log(msg):
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    try:
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    print(line, flush=True)


def get_secret():
    s = os.environ.get("SCAN_SECRET", "").strip()
    if s:
        return s
    env = HERE / "scan.env"
    if env.exists():
        for ln in env.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if ln.startswith("SCAN_SECRET="):
                return ln.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def call(path, secret, method="GET", payload=None):
    """Call Railway with the poller secret. Returns parsed JSON or None."""
    data = json.dumps(payload).encode() if payload is not None else None
    hdrs = {"X-Scan-Secret": secret, "User-Agent": "aismarketcap-scan-poller/1.0"}
    if data:
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(SITE + path, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        log(f"{path} -> HTTP {e.code}")
    except Exception as e:
        log(f"{path} -> {type(e).__name__}: {e}")
    return None


def acquire_lock():
    """Single-poller guard. A stale lock from a crash is broken by age."""
    try:
        LOCK.write_text(str(time.time()), encoding="utf-8")
        return True
    except Exception:
        return False


def lock_is_stale():
    if not LOCK.exists():
        return True
    try:
        return (time.time() - float(LOCK.read_text(encoding="utf-8").strip())) > 3600
    except Exception:
        return True


def run_scan():
    log("running daily_scan.ps1 ...")
    t0 = time.time()
    try:
        p = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", str(SCAN_PS1)],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=SCAN_TIMEOUT_S, cwd=str(HERE),
        )
        took = int(time.time() - t0)
        tail = (p.stdout or "")[-400:].replace("\n", " ")
        ok = p.returncode == 0
        log(f"scan finished rc={p.returncode} in {took}s :: {tail[:300]}")
        return ok, f"rc={p.returncode} in {took}s"
    except subprocess.TimeoutExpired:
        log(f"scan TIMED OUT after {SCAN_TIMEOUT_S}s")
        return False, "timeout"
    except Exception as e:
        log(f"scan error: {type(e).__name__}: {e}")
        return False, f"{type(e).__name__}"


def main():
    secret = get_secret()
    if not secret:
        print("FATAL: SCAN_SECRET not set (env var, or scan.env next to this file)")
        return 1
    if not SCAN_PS1.exists():
        print(f"FATAL: {SCAN_PS1} not found")
        return 1

    log(f"poller started, polling {SITE} every {POLL_S}s")
    backoff = POLL_S
    while True:
        try:
            if lock_is_stale():
                if not acquire_lock():
                    time.sleep(POLL_S)
                    continue
                res = call("/api/scan-poll", secret)
                if not res:
                    backoff = min(300, backoff * 2)
                    time.sleep(backoff)
                    continue
                backoff = POLL_S
                st = res.get("state")
                if st == "claimed":
                    ok, detail = run_scan()
                    call("/api/scan-complete", secret, "POST",
                         {"ok": ok, "detail": detail})
                    try:
                        LOCK.unlink()
                    except Exception:
                        pass
            time.sleep(POLL_S)
        except KeyboardInterrupt:
            log("poller stopped")
            return 0
        except Exception as e:
            log(f"loop error: {type(e).__name__}: {e}")
            time.sleep(POLL_S)


if __name__ == "__main__":
    sys.exit(main())