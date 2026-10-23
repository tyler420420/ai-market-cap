#!/usr/bin/env python3
"""Guard the growth work: no invented endorsements, a real capture path, and
a real alert sender.

WHY THIS EXISTS
---------------
Three findings from the 2026-10-22 live audit:

  1. The checkout page carried five five-star testimonials attributed to four
     invented customers, each with a specific gain. That is an FTC endorsement
     exposure and a trust problem the moment anyone looks closely.
  2. The only <input> on the entire site was the chat box - no email capture,
     no owned channel. A visitor not ready to pay was unreachable.
  3. The pricing page sold "real-time earnings alerts" and the repo contained
     no outbound transport at all.

Two earlier versions of these checks reported ALL PASS while matching NOTHING:
the testimonial regex looked for "&mdash;" where the page emits a literal
U+2014, and "subscribe" matched the nav button rather than a form. Every check
below therefore asserts on something that must be non-empty, and the
negative checks assert on a token that genuinely must be absent.

Run:  python verify_growth.py
Exit 0 = all pass.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

SITE = Path(r"C:\Users\Tyler_AI\ai-market-cap")
failures = []


def check(name, ok, detail=""):
    print(("PASS" if ok else "FAIL") + f"  {name}" + ("" if ok else f"  -- {detail}"))
    if not ok:
        failures.append(name)


def main():
    sys.path.insert(0, str(SITE))
    import scanner_web as S
    app = S.app
    app.config["TESTING"] = True
    C = app.test_client()

    # ── 1. no invented endorsements survive ─────────────────────────────
    print("=== Checkout page: no invented endorsements ===")
    pricing = C.get("/pricing").get_data(as_text=True)
    authors = re.findall(r'class=author[^>]*>(.*?)</div>', pricing, re.S)
    print(f"        named endorsements found: {len(authors)}")
    for a in authors:
        print(f"          {a.strip()[:60]}")
    check("exactly one author line remains, and it is the founder",
          len(authors) == 1 and "Tyler" in authors[0],
          f"found {len(authors)}: {authors}")
    check("no fabricated customer names anywhere in the rendered page",
          not re.search(r'\b(Marcus T|Kevin R|Priya S|James W)\b', pricing))
    check("no invented 5-star block remains", pricing.count("\u2605\u2605\u2605\u2605\u2605") <= 1,
          f"{pricing.count(chr(0x2605) * 5)} star blocks")

    # ── 2. real wins, not decoration ────────────────────────────────────
    print("\n=== Checkout page: real tracked wins ===")
    gains = re.findall(r'\+\d+(?:\.\d+)?%', pricing)
    check("pricing page shows real gains", len(gains) >= 3,
          f"only {len(gains)} gain figures - the strip may not be rendering")
    print(f"        gains on the checkout page: {gains[:6]}")
    check("wins link back to the case study",
          'href="/wins/' in pricing)
    check("annual nudge is anchored to a real win count",
          "tracked setups have run to their target" in pricing,
          "the nudge must not appear without evidence behind it")
    check("annual nudge links to the annual checkout",
          "/create-checkout?plan=annual" in pricing)

    # ── 3. email capture actually works ─────────────────────────────────
    print("\n=== Free page: email capture ===")
    anon = C.get("/").get_data(as_text=True)
    check("free page has an email input", bool(re.search(r'type=["\']email["\']', anon)))
    check("signup form posts to the endpoint", "/api/email-signup" in anon)
    check("signup form has a honeypot", 'id="dl-hp"' in anon)
    check("no build placeholder survives into the rendered page",
          "<!--REAL-WINS-STRIP-->" not in pricing,
          "the marker reached the customer - an injection step did not run")

    P = app.test_client()
    P.set_cookie("stripe_customer", "cus_VTsULOjOP83NeP", domain="localhost")
    sub_home = P.get("/").get_data(as_text=True)
    check("a paying customer is NEVER shown the signup form",
          'id="dl-signup"' not in sub_home,
          "we are upselling a paying customer for something he already has")

    lst = S.EMAIL_LIST_FILE
    backup = lst.read_text(encoding="utf-8") if lst.exists() else None
    try:
        if lst.exists():
            lst.unlink()
        r = C.post("/api/email-signup", json={"email": "not-an-email"})
        check("rejects a malformed address", r.status_code == 400, f"got {r.status_code}")
        r = C.post("/api/email-signup", json={"email": ""})
        check("rejects an empty address", r.status_code == 400, f"got {r.status_code}")
        r = C.post("/api/email-signup", json={"email": "a@b.co", "website": "bot"})
        check("honeypot swallows a bot without storing", r.status_code == 200)
        check("bot submission stored nothing",
              not lst.exists() or "a@b.co" not in lst.read_text(encoding="utf-8"))
        r = C.post("/api/email-signup", json={"email": "t@example.com"})
        check("accepts a valid address", r.status_code == 200, f"got {r.status_code}")
        data = json.loads(lst.read_text(encoding="utf-8"))
        check("the address is actually stored", "t@example.com" in data)
        r = C.post("/api/email-signup", json={"email": "t@example.com"})
        data2 = json.loads(lst.read_text(encoding="utf-8"))
        check("a repeat signup does not duplicate the record",
              len(data2) == len(data), f"{len(data)} -> {len(data2)}")
        check("a repeat signup increments instead of overwriting",
              data2["t@example.com"].get("seen_count", 1) >= 2,
              str(data2["t@example.com"]))
        r = C.post("/api/email-signup", data="not json",
                   content_type="application/json")
        check("survives a malformed body without a 500", r.status_code < 500,
              f"got {r.status_code}")
    finally:
        if backup is not None:
            lst.write_text(backup, encoding="utf-8")
        elif lst.exists():
            lst.unlink()

    # ── 4. the alert actually builds and knows it is unconfigured ───────
    print("\n=== Daily alert sender ===")
    p = subprocess.run([sys.executable, str(SITE / "send_daily_alert.py"),
                        "--dry-run"], capture_output=True, text=True, timeout=120)
    check("alert dry-run exits 0", p.returncode == 0, p.stdout[-160:] + p.stderr[-160:])
    check("alert builds a real subject from live scanner data",
          "is today's pick" in p.stdout, p.stdout[:200])
    check("alert reports its recipient count", "recipients:" in p.stdout)
    check("alert refuses to pretend it sent when unconfigured",
          "NOT CONFIGURED" in p.stdout or "sent=" in p.stdout,
          "a silent no-op would recreate the broken-promise defect")
    check("alert script never prints a credential",
          not re.search(r'ALERT_API_KEY\s*=\s*\S|pass(word)?=', p.stdout),
          "a dry-run must not echo secrets")

    # ── 5. the chat upsells the annual plan, not just monthly ───────────
    print("\n=== Chat annual nudge ===")
    reply = S.answer_from_data("how much does it cost")
    check("chat mentions the annual plan", "$50/year" in reply, reply[:120])
    check("chat no longer claims on-demand scans",
          "on-demand scans" not in reply, reply[:120])

    # ── 6. secrets and PII can never be committed ───────────────────────
    print("\n=== Secrets and PII ===")
    import subprocess as sp
    g = sp.run(["C:\\Program Files\\Git\\cmd\\git.exe", "-C", str(SITE),
                "check-ignore", "email_list.json", "alert.env"],
               capture_output=True, text=True)
    ignored = set(g.stdout.split())
    check("email_list.json is gitignored", "email_list.json" in ignored, g.stdout)
    check("alert.env is gitignored", "alert.env" in ignored, g.stdout)
    t = sp.run(["C:\\Program Files\\Git\\cmd\\git.exe", "-C", str(SITE),
                "ls-files", "--error-unmatch", "email_list.json"],
               capture_output=True, text=True)
    check("email_list.json is not tracked", t.returncode != 0)

    print(f"\n=== {'ALL PASS' if not failures else str(len(failures)) + ' FAILURE(S)'} ===")
    for f in failures:
        print(f"   - {f}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())