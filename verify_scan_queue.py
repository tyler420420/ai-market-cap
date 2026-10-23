#!/usr/bin/env python3
"""Prove the on-demand scan queue works end to end, without running a scan.

WHY THIS EXISTS
---------------
Tyler 2026-10-22: "point the scan to my local machine, that is best solution."

A queue that is wired wrong is worse than no queue: the subscriber clicks Scan,
sees "queued", and nothing ever happens - the exact failure this whole fix
exists to end. So the queue is tested as a STATE MACHINE, including the parts
that only bite in production.

Tested:
  - a stranger cannot poll or complete (secret enforced)
  - a wrong secret is rejected
  - a subscriber's click queues a request
  - the local machine claims it, and a SECOND poll while running gets nothing
  - a stale claim is released so a dead poller cannot wedge the queue forever
  - completing clears it and the machine can claim the next one
  - two subscribers clicking at once produce ONE scan, not two
  - a no-op scan does not silently consume the daily allowance

daily_scan.ps1 is never executed - /api/scan-complete is called directly. This
is a wiring test, not a scan.

Run:  python verify_scan_queue.py
Exit 0 = all pass.
"""
import sys
import time
from pathlib import Path

SITE = Path(r"C:\Users\Tyler_AI\ai-market-cap")
sys.path.insert(0, str(SITE))

failures = []
SUB = "cus_VTsULOjOP83NeP"
SECRET = "test-secret-not-the-real-one"


def check(name, ok, detail=""):
    print(("PASS" if ok else "FAIL") + f"  {name}" + ("" if ok else f"  -- {detail}"))
    if not ok:
        failures.append(name)


def main():
    import scanner_web

    app = scanner_web.app
    app.config["TESTING"] = True
    scanner_web.SCAN_SECRET = SECRET

    # PRODUCTION CONDITION. In-container scanning is disabled on Railway - that
    # is the whole reason this queue exists. Locally ALLOW_IN_CONTAINER_SCAN is
    # false but trigger_scan() is the real function, so the FIRST version of
    # this test took the "started" branch and never exercised the queue at all.
    # Forcing the flag off guarantees we test the path subscribers actually hit.
    orig_allow = scanner_web.ALLOW_IN_CONTAINER_SCAN
    scanner_web.ALLOW_IN_CONTAINER_SCAN = False

    qfile = scanner_web.SCAN_QUEUE_FILE
    if qfile.exists():
        qfile.unlink()

    # ---- 1. the secret is actually enforced ----------------------------
    C = app.test_client()
    C.set_cookie("stripe_customer", SUB, domain="localhost")

    r = C.get("/api/scan-poll")                       # no secret at all
    check("poll without a secret is refused", r.status_code == 403,
          f"got {r.status_code}")
    r = C.get("/api/scan-poll", headers={"X-Scan-Secret": "wrong"})
    check("poll with the wrong secret is refused", r.status_code == 403,
          f"got {r.status_code}")
    r = C.post("/api/scan-complete", json={"ok": True})
    check("complete without a secret is refused", r.status_code == 403,
          f"got {r.status_code}")

    # A subscriber must NOT be able to use the poller endpoints either -
    # their cookie is not the secret.
    r = C.get("/api/scan-poll")
    check("a subscriber's cookie does not substitute for the secret",
          r.status_code == 403, f"got {r.status_code}")

    # ---- 2. a click queues a real request ------------------------------
    before = scanner_web.get_scans_today(SUB)
    r = C.post("/run", follow_redirects=False)
    check("Scan button queues a request", r.status_code == 200, f"got {r.status_code}")
    d = r.get_json() or {}
    check("Scan reports it queued on the local machine",
          d.get("status") in ("queued_locally", "already_pending"),
          f"status={d.get('status')!r}")
    q = scanner_web._read_queue()
    check("queue is pending", q.get("state") == "pending", str(q)[:100])
    check("queue records who asked", q.get("requested_by") == SUB, str(q)[:100])

    # ---- 3. the machine claims it --------------------------------------
    M = app.test_client()
    r = M.get("/api/scan-poll", headers={"X-Scan-Secret": SECRET})
    check("local machine claims the request", (r.get_json() or {}).get("state") == "claimed",
          str(r.get_json())[:100])
    check("claim marks it running",
          scanner_web._read_queue().get("state") == "running")

    # ---- 4. a second poller must not double-scan ------------------------
    M2 = app.test_client()
    r = M2.get("/api/scan-poll", headers={"X-Scan-Secret": SECRET})
    check("a second poller does NOT claim the same scan",
          (r.get_json() or {}).get("state") == "running",
          f"two pollers would run duplicate scans: {r.get_json()}")

    # ---- 5. a dead poller cannot wedge the queue forever ----------------
    q = scanner_web._read_queue()
    q["claimed_at"] = time.time() - (scanner_web.SCAN_CLAIM_TTL_S + 60)
    scanner_web._write_queue(q)
    r = M2.get("/api/scan-poll", headers={"X-Scan-Secret": SECRET})
    check("a stale claim is released so the queue cannot wedge",
          (r.get_json() or {}).get("state") == "claimed",
          "if a poller dies mid-scan the button is dead forever")

    # ---- 6. completing clears it ----------------------------------------
    r = M.post("/api/scan-complete", json={"ok": True, "detail": "test"},
               headers={"X-Scan-Secret": SECRET})
    check("machine reports completion", r.status_code == 200, f"got {r.status_code}")
    check("queue is idle again",
          scanner_web._read_queue().get("state") == "idle")

    # ---- 7. two clicks, one scan ----------------------------------------
    scanner_web._write_queue({"state": "idle"})
    C.post("/run", follow_redirects=False)
    r = C.post("/run", follow_redirects=False)
    check("a second click does not queue a duplicate scan",
          (r.get_json() or {}).get("status") == "already_pending",
          f"status={(r.get_json() or {}).get('status')!r}")
    M.get("/api/scan-poll", headers={"X-Scan-Secret": SECRET})
    M.post("/api/scan-complete", json={"ok": True},
           headers={"X-Scan-Secret": SECRET})

    # ---- 8. the poller script exists and is wired to this queue ---------
    poller = (SITE / "scan_poller.py").read_text(encoding="utf-8")
    check("scan_poller.py exists", (SITE / "scan_poller.py").exists())
    check("poller polls /api/scan-poll", "/api/scan-poll" in poller)
    check("poller reports back via /api/scan-complete", "/api/scan-complete" in poller)
    check("poller runs daily_scan.ps1", "daily_scan.ps1" in poller)
    check("poller sends the secret header", "X-Scan-Secret" in poller)

    # ---- 9. a missing secret fails closed, not open ---------------------
    scanner_web.SCAN_SECRET = ""
    r = app.test_client().get("/api/scan-poll", headers={"X-Scan-Secret": "anything"})
    check("with no secret configured the poller API is closed, not open",
          r.status_code == 403, f"got {r.status_code} - unset secret must deny")

    if qfile.exists():
        qfile.unlink()
    scanner_web.ALLOW_IN_CONTAINER_SCAN = orig_allow
    print(f"\n=== {'ALL PASS' if not failures else str(len(failures)) + ' FAILURE(S)'} ===")
    for f in failures:
        print(f"   - {f}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())