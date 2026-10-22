#!/usr/bin/env python3
"""Prove the fixed trending-card guard actually bites.

WHY THIS EXISTS
---------------
The guard regressed in the worst possible direction: it asserted a hardcoded
list of FALLBACK company names, so it PASSED when the IPO scrape was broken
and the fallback list was used, and FAILED when the real scrape worked and
rendered a real company. That inverted the guard completely. On 2026-10-21
both daily scans refused to deploy perfectly good HTML because the fetch
started succeeding.

A guard nobody has watched fail is an assumption. So this script takes the
REAL artifact and reinstates each defect in a throwaway copy, then confirms
the guard catches every one of them:

  defect 1  all four cards emptied          -> must FAIL
  defect 2  only the IPO card emptied        -> must FAIL
  defect 3  only the ETF card emptied        -> must FAIL
  defect 4  IPO placeholder text ships       -> must FAIL
  defect 5  card anchor renders empty text   -> must FAIL
  defect 6  card anchor is href="#"          -> must FAIL

And the control:

  clean     the real artifact, unmodified   -> must PASS

Every defect is injected into a COPY in a temp dir. The real artifact and the
real verify_output.py are never touched.

Run:  python prove_verify_output_bites.py
Exit 0 = the guard catches every defect (good). Exit 1 = a defect slipped
through, which means the guard is not trustworthy.
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SRC = Path(r"C:\Users\Tyler_AI\ai-market-cap")
REAL_HTML = SRC / "ai_earnings_today.html"
VERIFY = SRC / "verify_output.py"
PY = sys.executable


def run_guard(html_path):
    """Run verify_output.py against a specific HTML file. Returns exit code."""
    tmpdir = Path(tempfile.mkdtemp(prefix="bites_"))
    try:
        # Copy the verifier and point it at our HTML by writing it beside the
        # verifier with the exact filename verify_output.py expects.
        v = tmpdir / "verify_output.py"
        shutil.copy2(VERIFY, v)
        h = tmpdir / "ai_earnings_today.html"
        shutil.copy2(html_path, h)
        r = subprocess.run([PY, str(v)], capture_output=True, text=True, timeout=120)
        return r.returncode, r.stdout
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def card_span(html, label):
    """(start, end) of the card whose label is `label`. Raises if absent."""
    i = html.find(label)
    if i < 0:
        raise AssertionError(f"label {label!r} not present in artifact")
    rest_i = i + len(label)
    stops = [p for p in (rest_i + html[rest_i:].find(l)
                         for l in ("TRENDING IPO", "TRENDING METAL",
                                   "TRENDING UTILITY", "TRENDING ETF"))
             if p >= rest_i]
    nxt = min(stops) if stops else rest_i + 600
    return rest_i, min(nxt, rest_i + 600)


def empty_all_cards(html):
    """Replace every card body with the 'No data' empty state."""
    for label in ("TRENDING IPO", "TRENDING METAL",
                  "TRENDING UTILITY", "TRENDING ETF"):
        s, e = card_span(html, label)
        block = html[s:e]
        # Strip the anchor, and inject the literal empty-state marker.
        block2 = re.sub(r'<a\s[^>]*href="[^"]*"[^>]*>[^<]*</a>', "", block)
        if "No data" not in block2:
            block2 = block2 + '<div>No data</div>'
        html = html[:s] + block2 + html[e:]
    return html


def empty_named_card(html, label):
    """Empty exactly one card, leaving the other three intact."""
    s, e = card_span(html, label)
    block = re.sub(r'<a\s[^>]*href="[^"]*"[^>]*>[^<]*</a>', "", html[s:e])
    if "No data" not in block:
        block += '<div>No data</div>'
    return html[:s] + block + html[e:]


def add_placeholder(html):
    return html + '<div>No upcoming IPOs</div>'


def blank_anchor_text(html):
    """Keep the anchor but empty its text - a card with a link and no label."""
    label = "TRENDING IPO"
    s, e = card_span(html, label)
    block = re.sub(r'(<a\s[^>]*href="[^"]*"[^>]*>)[^<]*(</a>)',
                   r'\1\2', html[s:e])
    return html[:s] + block + html[e:]


def href_is_hash(html):
    """Keep the anchor text but make the href a dead '#' link."""
    label = "TRENDING ETF"
    s, e = card_span(html, label)
    block = re.sub(r'(<a\s[^>]*href=")[^"]*(")', r'\1#\2', html[s:e])
    return html[:s] + block + html[e:]


MUTATIONS = [
    ("all four cards emptied", empty_all_cards, "every card empty"),
    ("only IPO card emptied", lambda h: empty_named_card(h, "TRENDING IPO"),
     "IPO card empty, others intact"),
    ("only ETF card emptied", lambda h: empty_named_card(h, "TRENDING ETF"),
     "ETF card empty, others intact"),
    ("'No upcoming IPOs' placeholder", add_placeholder,
     "historical empty-state regression"),
    ("card anchor has empty text", blank_anchor_text,
     "link present but no company name"),
    ("card anchor href is '#'", href_is_hash,
     "dead link with visible text"),
]


def main():
    if not REAL_HTML.exists():
        print(f"FATAL: {REAL_HTML} not found - run a scan first")
        return 1

    base = REAL_HTML.read_text(encoding="utf-8")
    tmp = Path(tempfile.mkdtemp(prefix="bites_src_"))
    failed = 0
    try:
        # ---- control: the real artifact must PASS -----------------------
        rc, out = run_guard(REAL_HTML)
        ok = (rc == 0)
        print(f"{'PASS' if ok else 'FAIL'}  control: real artifact passes "
              f"(exit {rc})")
        if not ok:
            print("      the guard rejects today's real artifact - "
                  "fix that before trusting any mutation result")
            for ln in out.splitlines():
                if "FAIL" in ln:
                    print("      " + ln.strip())
        failed += (not ok)

        # ---- each defect must be CAUGHT ---------------------------------
        for name, mut, why in MUTATIONS:
            mutated = mut(base)
            changed = mutated != base
            f = tmp / (re.sub(r"\W+", "_", name) + ".html")
            f.write_text(mutated, encoding="utf-8")
            rc, out = run_guard(f)
            caught = (rc != 0)
            print(f"{'PASS' if caught else 'FAIL'}  catches: {name} "
                  f"(exit {rc})")
            if not changed:
                print(f"      WARNING: mutation {name!r} did not change the "
                      "artifact - the test is not exercising what it claims")
                failed += 1
                continue
            if caught:
                hit = [ln.strip() for ln in out.splitlines()
                       if "FAIL" in ln and "card" in ln.lower()]
                for ln in hit[:2]:
                    print("      caught: " + ln)
            else:
                print(f"      NOT CAUGHT - a page with {why} would ship")
                failed += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    total = len(MUTATIONS) + 1
    print(f"\n=== {total - failed}/{total} PASS ===")
    if failed:
        print("the guard is NOT trustworthy - it missed a real defect")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())