#!/usr/bin/env python3
"""Verify the email list transport: export, unsubscribe, and PII handling.

WHY THIS EXISTS
The free-page signup wrote to EMAIL_LIST_FILE inside Railway's container and
the sender read a LOCAL copy, so the two never met. Signups were captured,
answered "Check your inbox tomorrow morning", and lost on the next deploy.
A token-protected export is the fix, and an export is the single route on the
whole site that emits addresses - so it is the route where a mistake is
expensive and silent.

Every check runs against a TEMP file. The guard never reads or writes the real
email_list.json: a verification suite that mutates production PII is itself a
PII leak, and it would also mean running the guard could change who gets mail.
"""
import json
import os
import subprocess as sp
import sys
import tempfile
from pathlib import Path

SITE = Path(__file__).parent
sys.path.insert(0, str(SITE))

TOKEN = "verify-only-not-a-real-secret-0123456789"
FAILURES = []


def check(label, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", label,
                          "" if ok else "  <- " + str(detail)[:300]))
    if not ok:
        FAILURES.append(label)
    return ok


def section(title):
    print("\n=== %s ===" % title)


def main():
    import scanner_web as W
    import send_daily_alert as A
    import email_unsubscribe as EU
    import pull_email_list as P

    tmpdir = tempfile.mkdtemp(prefix="emaillist_verify_")
    tmp = Path(tmpdir) / "email_list.json"

    # Redirect the module's file at a temp path for the whole run.
    real_file = W.EMAIL_LIST_FILE
    W.EMAIL_LIST_FILE = tmp
    real_token = W.EMAIL_EXPORT_TOKEN
    try:
        client = W.app.test_client()

        section("An unset token denies everything - fails closed")
        W.EMAIL_EXPORT_TOKEN = ""
        r = client.get("/api/email-list-export")
        check("export is 403 with no token configured",
              r.status_code == 403, r.status_code)
        r = client.post("/api/email-unsubscribe?t=anything.x")
        check("unsubscribe is 503 with no token configured",
              r.status_code == 503, r.status_code)
        check("a denied export returns no addresses",
              b"list" not in (r.data or b""), r.data[:200])

        W.EMAIL_EXPORT_TOKEN = TOKEN

        section("The export requires the exact token")
        r = client.get("/api/email-list-export")
        check("export with no header is 403", r.status_code == 403, r.status_code)
        r = client.get("/api/email-list-export",
                       headers={"X-Email-Token": "wrong-token"})
        check("export with the wrong token is 403",
              r.status_code == 403, r.status_code)
        r = client.get("/api/email-list-export",
                       headers={"X-Email-Token": TOKEN})
        check("export with the right token is 200",
              r.status_code == 200, r.status_code)
        cc = (r.headers.get("Cache-Control") or "")
        check("export is never cached", "no-store" in cc, cc)

        section("Signup and export agree")
        a = "verify.free@example.com"
        b = "verify.paid@example.com"
        r = client.post("/api/email-signup", json={"email": a})
        check("signup accepted", r.status_code == 200, r.status_code)
        client.post("/api/email-signup", json={"email": b})
        r = client.get("/api/email-list-export",
                       headers={"X-Email-Token": TOKEN})
        body = r.get_json() or {}
        check("export count matches the list",
              body.get("count") == 2, body.get("count"))
        check("both addresses are present",
              a in (body.get("list") or {}) and b in (body.get("list") or {}),
              sorted((body.get("list") or {}).keys()))

        section("One-click unsubscribe is unforgeable")
        link = W.unsubscribe_link(a)
        check("link points at the unsubscribe route",
              link.startswith("https://aismarketcap.com/api/email-unsubscribe"),
              link[:60])
        check("the address is not readable in the URL",
              a not in link and "example.com" not in link, link[:90])

        forged = link[:-1] + ("0" if link[-1] != "0" else "1")
        r = client.post("/api/email-unsubscribe?t=" + forged)
        check("a forged signature is rejected 400",
              r.status_code == 400, r.status_code)
        r = client.post("/api/email-unsubscribe?t=garbage")
        check("a junk token is rejected 400", r.status_code == 400, r.status_code)

        raw = link.split("?t=", 1)[1]
        r = client.post("/api/email-unsubscribe?t=" + raw)
        check("a valid token is accepted 200", r.status_code == 200, r.status_code)
        r = client.get("/api/email-list-export",
                       headers={"X-Email-Token": TOKEN})
        body = r.get_json() or {}
        check("the address is now marked unsubscribed",
              bool((body.get("list") or {}).get(a, {}).get("unsubscribed")),
              (body.get("list") or {}).get(a))
        check("the other address is NOT unsubscribed",
              not (body.get("list") or {}).get(b, {}).get("unsubscribed"),
              (body.get("list") or {}).get(b))

        # ---- a pasted secret must not fail silently ---------------------
        # A token pasted into a dashboard can arrive with a trailing newline
        # or a stray CRLF. The presented header is stripped but the STORED
        # value used to be compared unstripped, so the export compared
        # unequal while every other check still looked healthy: the homepage
        # promise said "delivery ready", the unsubscribe route answered 200,
        # and only the export 403ed - so the free list could never be pulled
        # home and nothing anywhere reported it.
        section("A token pasted with a stray newline still works")
        W.EMAIL_EXPORT_TOKEN = TOKEN + "\n"
        r = client.get("/api/email-list-export",
                       headers={"X-Email-Token": TOKEN})
        check("a stored token with a trailing newline still exports",
              r.status_code == 200, r.status_code)
        r = client.get("/api/email-list-export",
                       headers={"X-Email-Token": "  " + TOKEN + "  "})
        check("a presented token with surrounding spaces also exports",
              r.status_code == 200, r.status_code)
        r = client.get("/api/email-list-export",
                       headers={"X-Email-Token": "wrong-token"})
        check("normalizing does not weaken it - a wrong token is still 403",
              r.status_code == 403, r.status_code)
        W.EMAIL_EXPORT_TOKEN = "\t" + TOKEN + "  \r\n"
        r = client.get("/api/email-list-export",
                       headers={"X-Email-Token": TOKEN})
        check("surrounding whitespace and CRLF still export",
              r.status_code == 200, r.status_code)
        check("and delivery still reads ready",
              W._delivery_ready() is True)
        W.EMAIL_EXPORT_TOKEN = '"' + TOKEN + '"'
        r = client.get("/api/email-list-export",
                       headers={"X-Email-Token": TOKEN})
        check("a stored token pasted inside quotes still exports",
              r.status_code == 200, r.status_code)
        W.EMAIL_EXPORT_TOKEN = TOKEN + '"'
        r = client.get("/api/email-list-export",
                       headers={"X-Email-Token": TOKEN})
        check("a lone trailing quote is CONTENT, not whitespace - still 403",
              r.status_code == 403, r.status_code)

        # A whitespace-only token is a paste accident, not a configuration.
        # It must read as NOT configured everywhere, or the route answers 400
        # ("bad token"), which every health check mistakes for "working".
        W.EMAIL_EXPORT_TOKEN = "   \n"
        check("a whitespace-only token is not delivery-ready",
              W._delivery_ready() is False)
        r = client.get("/api/email-list-export",
                       headers={"X-Email-Token": "   "})
        check("a whitespace-only token denies the export",
              r.status_code == 403, r.status_code)
        r = client.post("/api/email-unsubscribe?t=anything.x")
        check("a whitespace-only token is not configured for unsubscribe",
              r.status_code == 503, r.status_code)

        # The HMAC half. The link is minted on THIS machine with the clean
        # secret and verified on the service. If the service stores the same
        # secret with a newline and does not normalize it, every recipient's
        # unsubscribe click 400s - the mail sends fine and the failure is
        # invisible until a customer complains.
        W.EMAIL_EXPORT_TOKEN = TOKEN + "\n"
        clean = EU.unsubscribe_token("newline@example.com", TOKEN)
        check("a link minted with the clean secret verifies against a "
              "newline-stored secret",
              EU.parse_unsubscribe(clean, TOKEN + "\n") == "newline@example.com",
              EU.parse_unsubscribe(clean, TOKEN + "\n"))
        r = client.post("/api/email-unsubscribe?t=" + clean)
        check("and the live route accepts that link (200)",
              r.status_code == 200, r.status_code)
        check("a whitespace-only key mints no link at all",
              EU.unsubscribe_link("x@example.com", "   ") is None)
        W.EMAIL_EXPORT_TOKEN = TOKEN

        section("GET renders a page, POST answers the mail client")
        r = client.get("/api/email-unsubscribe?t=" + raw)
        check("GET returns HTML for a human",
              r.status_code == 200 and b"unsubscribed" in (r.data or b"").lower(),
              r.status_code)

        section("PII never reaches git")
        g = sp.run([r"C:\Program Files\Git\cmd\git.exe", "-C", str(SITE),
                    "check-ignore", "email_list.json"],
                   capture_output=True, text=True)
        check("email_list.json is gitignored", "email_list.json" in g.stdout,
              g.stdout)
        t = sp.run([r"C:\Program Files\Git\cmd\git.exe", "-C", str(SITE),
                    "ls-files", "--error-unmatch", "email_list.json"],
                   capture_output=True, text=True)
        check("email_list.json is not tracked", t.returncode != 0)
        g = sp.run([r"C:\Program Files\Git\cmd\git.exe", "-C", str(SITE),
                    "check-ignore", "alert.env"], capture_output=True, text=True)
        check("alert.env is gitignored", "alert.env" in g.stdout, g.stdout)

        # ---- cross-process round trip -----------------------------------
        # The link is built on THIS machine and verified on Railway. If the
        # two halves disagreed the mail would still send fine and every
        # unsubscribe would 400 in a container nobody is reading logs from.
        section("The link this machine builds, Railway accepts")
        env = {"EMAIL_EXPORT_TOKEN": TOKEN}
        who = "roundtrip@example.com"
        link = A.unsubscribe_url(who, env)
        check("the sender builds a link", bool(link) and "aismarketcap.com" in link,
              link)
        tok = link.split("?t=", 1)[1]
        check("it verifies under the shared module",
              EU.parse_unsubscribe(tok, TOKEN) == who,
              EU.parse_unsubscribe(tok, TOKEN))
        check("Railway's route accepts that exact token",
              client.post("/api/email-unsubscribe?t=" + tok).status_code == 200)
        check("a token built with the WRONG secret does not verify",
              EU.parse_unsubscribe(tok, "some-other-secret") is None)

        section("Suppression actually stops the send")
        FIX_LIST = {
            "kept@example.com": {"seen_count": 1},
            "gone@example.com": {"seen_count": 1, "unsubscribed": "2026-10-22"},
        }
        # Two ACTIVE subscriptions on ONE email address. This is the live
        # shape as of 2026-10-23: Stripe holds two active subs, both on
        # tyler@tribunefunding.com. That is $10 MRR and ONE customer, and a
        # dedup that keys on anything but the address would mail the owner
        # two copies of every daily pick with nothing anywhere reporting it.
        FIX_SUBS = {"cus_x": {"status": "active", "email": "paying@example.com"},
                    "cus_y": {"status": "active", "email": "paying@example.com"},
                    "cus_z": {"status": "active", "email": "gone@example.com"}}
        real_load = A.load_json

        def fake_load(name, default):
            return {"email_list.json": FIX_LIST,
                    "subscriptions.json": FIX_SUBS}.get(name, default)
        A.load_json = fake_load
        try:
            got = dict(A.recipients())
            check("a free address is still mailed", got.get("kept@example.com") is False,
                  got)
            check("an unsubscribed free address is NOT mailed",
                  "gone@example.com" not in got, got)
            check("a paying address is still mailed", got.get("paying@example.com") is True,
                  got)
            rc = A.recipients()
            dupes = [e for e in rc if [r[0] for r in rc].count(e) > 1]
            check("two subs on one address produce ONE email, not two",
                  rc.count(("paying@example.com", True)) == 1 and not dupes,
                  [(r, rc.count(r)) for r in rc])
            total, active, dead = A.list_stats()
            check("list_stats counts the suppression", (total, active, dead) == (2, 1, 1),
                  (total, active, dead))
        finally:
            A.load_json = real_load

        section("Every message carries a real unsubscribe")
        for tier in (False, True):
            html, _ = A.build_email(paid=tier)
            if html is None:
                check("built the %s variant" % ("paid" if tier else "free"), False,
                      "no scanner data to build from")
                continue
            rendered = A.render_unsub(html, "someone@example.com", env)
            check("the %s variant has no leftover placeholder"
                  % ("paid" if tier else "free"),
                  A.UNSUB_PLACEHOLDER not in rendered)
            check("the %s variant has an unsubscribe link"
                  % ("paid" if tier else "free"),
                  "Unsubscribe" in rendered and "aismarketcap.com" in rendered)

        # ---- the merge rule ---------------------------------------------
        # This is the most dangerous line in the lane. The remote list lives
        # on an ephemeral container disk, so "not on the remote" almost always
        # means "signed up before the last restart", NOT "unsubscribed". A
        # merge that deleted absent entries would unsubscribe the entire list
        # on the next deploy, silently and irreversibly.
        section("A pull never deletes, and never resurrects an unsubscribe")

        LOCAL = {
            "keep@example.com": {"seen_count": 3, "last_seen": "old"},
            "gone@example.com": {"seen_count": 1,
                                 "unsubscribed": "2026-10-22T10:00:00"},
        }
        REMOTE = {
            "keep@example.com": {"seen_count": 4, "last_seen": "new"},
            "gone@example.com": {"seen_count": 1, "last_seen": "new"},
            "fresh@example.com": {"seen_count": 1, "last_seen": "new"},
        }
        out, added, refreshed, unsubs = P.merge(dict(LOCAL), REMOTE)
        check("a new address is added", "fresh@example.com" in out, sorted(out))
        check("an existing address is refreshed, not duplicated",
              out.get("keep@example.com", {}).get("seen_count") == 4,
              out.get("keep@example.com"))
        check("seen_count takes the higher of the two, never a lower value",
              out["keep@example.com"]["seen_count"] == 4,
              out["keep@example.com"])
        check("an unsubscribed address STAYS unsubscribed after a deploy",
              bool(out.get("gone@example.com", {}).get("unsubscribed")),
              out.get("gone@example.com"))
        check("counters report the shape of the pull",
              (added, unsubs) == (1, 0), (added, refreshed, unsubs))

        # A remote that is empty must not empty the local list.
        out2, added2, _, _ = P.merge(dict(LOCAL), {})
        check("an EMPTY remote does not empty the local list",
              len(out2) == len(LOCAL), sorted(out2))
        check("an empty remote still preserves an unsubscribe",
              bool(out2.get("gone@example.com", {}).get("unsubscribed")),
              out2.get("gone@example.com"))

        # An unsubscribe that arrives from Railway must take effect.
        out3, _, _, uns3 = P.merge(
            {"x@example.com": {"seen_count": 1}},
            {"x@example.com": {"seen_count": 1, "unsubscribed": "2026-10-23"}})
        check("an unsubscribe arriving from Railway takes effect",
              uns3 == 1 and bool(out3["x@example.com"]["unsubscribed"]),
              (uns3, out3["x@example.com"]))

        # ---- tier precedence --------------------------------------------
        # A DIFFERENT bug from the duplicate one above, and a count-only
        # check cannot see either of them.
        #
        # The free list is appended before the paid list, so a plain
        # first-wins dedup hands the collision to the FREE tier. A customer
        # who pays AND once signed up free is then sent the free email: no
        # entry, no targets, no stop - silently downgraded, and the run log
        # files them under the free list so a successful run looks normal.
        #
        # It fires the moment the free list starts working, because until
        # then no address was on both lists at once.
        section("The paid tier wins an address that is on both lists")

        def run_recipients(free, subs):
            rl = A.load_json

            def fl(name, default):
                return {"email_list.json": free,
                        "subscriptions.json": subs}.get(name, default)
            A.load_json = fl
            try:
                return A.recipients()
            finally:
                A.load_json = rl

        both = run_recipients(
            {"buyer@example.com": {"seen_count": 1}},
            {"cus_1": {"status": "active", "email": "buyer@example.com"}})
        check("a buyer on both lists is sent the PAID email",
              both == [("buyer@example.com", True)], both)
        check("the free tier did not win the collision",
              not any(p is False for _, p in both), both)

        messy = run_recipients(
            {"  Buyer@Example.COM  ": {"seen_count": 1}},
            {"cus_1": {"status": "active", "email": "buyer@example.com"}})
        check("casing and padding on the free list cannot leak the free tier",
              messy == [("buyer@example.com", True)], messy)

        check("a free-only address is still sent free",
              run_recipients({"f@example.com": {"seen_count": 1}}, {})
              == [("f@example.com", False)])
        check("a paid-only address is sent paid",
              run_recipients({}, {"cus_1": {"status": "active",
                                            "email": "p@example.com"}})
              == [("p@example.com", True)])
        check("one address yields exactly ONE send, paid",
              len(both) == 1 and both[0][1] is True, both)

        # And the end-to-end consequence: the variant actually chosen.
        rcpt = dict(run_recipients(
            {"buyer@example.com": {"seen_count": 1}},
            {"cus_1": {"status": "active", "email": "buyer@example.com"}}))
        variants = A.build_variants()
        chosen = variants.get(rcpt["buyer@example.com"])[0]
        check("the buyer receives the variant WITH targets",
              "Available in Pro" not in chosen, "got the free variant")

        # ---- the signup response must not lie ---------------------------
        # This endpoint answered "Check your inbox tomorrow morning."
        # unconditionally while the list could not move. It is the promise
        # that made the whole failure invisible, so the message itself is
        # now part of the contract.
        section("The signup response tells the truth about delivery")

        ready_tok, was_tok = W.EMAIL_EXPORT_TOKEN, W.EMAIL_LIST_FILE
        cap_file = Path(tempfile.mkdtemp()) / "capture.json"

        def signup(email, **kw):
            rl = W.EMAIL_LIST_FILE
            W.EMAIL_LIST_FILE = cap_file
            try:
                r = client.post("/api/email-signup", json={"email": email}, **kw)
                return r.status_code, (r.get_json() or {})
            finally:
                W.EMAIL_LIST_FILE = rl

        try:
            W.EMAIL_EXPORT_TOKEN = ""
            code, j = signup("honest@example.com")
            check("an unconfigured signup returns 200", code == 200, code)
            check("it reports delivery is NOT ready",
                  j.get("delivery_ready") is False, j)
            check("it does NOT promise delivery",
                  "tomorrow" not in (j.get("message") or "").lower(), j)
            check("the promise string is absent entirely",
                  "Check your inbox tomorrow" not in (j.get("message") or ""), j)
            check("the address is STILL CAPTURED (the funnel survives)",
                  "honest@example.com" in
                  json.loads(cap_file.read_text(encoding="utf-8")),
                  cap_file.read_text(encoding="utf-8")[:120])

            _, honey = signup("bot@example.com", )
            W2 = client.post("/api/email-signup",
                             json={"email": "bot2@example.com", "website": "x"})
            hj = W2.get_json() or {}
            check("the honeypot returns the SAME shape (no configuration oracle)",
                  hj.get("delivery_ready") == j.get("delivery_ready")
                  and hj.get("message") == j.get("message"), (hj, j))

            W.EMAIL_EXPORT_TOKEN = TOKEN
            code, j2 = signup("ready@example.com")
            check("a configured signup reports delivery IS ready",
                  j2.get("delivery_ready") is True, j2)
            check("and only then promises tomorrow",
                  "tomorrow" in (j2.get("message") or "").lower(), j2)
        finally:
            W.EMAIL_EXPORT_TOKEN = ready_tok
            W.EMAIL_LIST_FILE = was_tok
            for p in (cap_file,):
                try:
                    p.unlink()
                    p.parent.rmdir()
                except Exception:
                    pass

        js = W.EMAIL_CAPTURE
        check("the client no longer paints not-ready in success green",
              "'warn'" in js and "delivery_ready===false" in js)
        check("the client has no hardcoded delivery promise left",
              "Check your inbox tomorrow morning.'" not in js)

    finally:
        W.EMAIL_LIST_FILE = real_file
        W.EMAIL_EXPORT_TOKEN = real_token
        try:
            tmp.unlink()
            os.rmdir(tmpdir)
        except Exception:
            pass

    print("\n=== %s ===" % ("ALL PASS" if not FAILURES
                           else str(len(FAILURES)) + " FAILURE(S)"))
    for f in FAILURES:
        print("  - " + f)
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())