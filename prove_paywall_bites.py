#!/usr/bin/env python3
"""Mutation-test verify_paywall.py.

WHY
---
Every guard in this repo has been caught passing while the product was broken
(verify_output.py asserted on a FALLBACK value, so it went green when the
scraper failed). A guard that has never been shown to fail is a comment.

So each mutation below re-introduces one real defect we already hit, runs
verify_paywall.py, and requires a NON-ZERO exit. The final run is the control:
clean tree must exit 0. If a mutation is reported "NOT CAUGHT" the guard is
decorative.

Mutations, each a bug that actually occurred:
  M1  _strip_pro_values returns the page untouched  (the original leak)
  M2  closing <!--/PROVALUES--> deleted from artifact (unpaired opener)
  M3  <!--PROVALUES--> moved AFTER the metric boxes (strip is empty)
  M4  _strip_element matches id= only (Runner Up uses class=)
  M5  _strip_block returns the page untouched (upsell stays for payers)

Run:  python prove_paywall_bites.py
Exit 0 = every mutation caught AND the clean control passes.
"""
import subprocess
import sys
from pathlib import Path

SITE = Path(r"C:\Users\Tyler_AI\ai-market-cap")
WEB = SITE / "scanner_web.py"
ART = SITE / "ai_earnings_today.html"
GUARD = SITE / "verify_paywall.py"
PY = sys.executable

web_orig = WEB.read_text(encoding="utf-8")
art_orig = ART.read_text(encoding="utf-8")

OPEN = "<!--PROVALUES-->"
CLOSE = "<!--/PROVALUES-->"

# Each mutation re-introduces one defect that actually occurred.
# A mutation may patch more than one file: (name, [(target, old, new), ...])
# `old` must exist verbatim in the clean file, or the run reports
# MUTATION-NOT-APPLIED rather than quietly counting a miss as a pass.
MUTATIONS = [
    (
        "M1 _strip_pro_values does nothing (the original leak)",
        [(WEB, "    while True:\n        i = content.find(VALUES_OPEN)",
          "    return content\n    while True:\n        i = content.find(VALUES_OPEN)")],
    ),
    (
        "M2 closing PROVALUES marker deleted from the artifact",
        [(ART, CLOSE, "")],
    ),
    (
        "M3 PROVALUES opener moved AFTER the metric boxes",
        [(ART, OPEN + '<span', CLOSE + '<span')],
    ),
    (
        "M4 the original 2026-10-22 code path restored (both overlays survive)",
        [
            (WEB, "    while True:\n        i = content.find(marker)",
             "    i = content.find(marker)\n    if i != -1:\n"
             "        j = content.find(close, i)\n        if j != -1:\n"
             "            return content[:i] + content[j + len(close):]\n    return content\n"
             "    while True:\n        i = content.find(marker)"),
            (WEB, '<div[^>]*(?:id|class)="%s"[^>]*>',
             '<div[^>]*id="%s"[^>]*>'),
        ],
    ),
    (
        "M5 _strip_block only removes the FIRST CTA, overlay button survives",
        [(WEB, "    while True:\n        i = content.find(marker)",
          "    if True:\n        i = content.find(marker)\n        if i == -1:\n"
          "            return content\n        j = content.find(close, i)\n"
          "        if j == -1:\n            return content\n"
          "        return content[:i] + content[j + len(close):]\n"
          "    while True:\n        i = content.find(marker)")],
    ),
]


def restore():
    WEB.write_text(web_orig, encoding="utf-8")
    ART.write_text(art_orig, encoding="utf-8")


def run_guard():
    p = subprocess.run([PY, str(GUARD)], capture_output=True, text=True,
                       cwd=str(SITE), timeout=600)
    return p.returncode, p.stdout + p.stderr


def main():
    results = []
    try:
        for name, patches in MUTATIONS:
            texts = {WEB: web_orig, ART: art_orig}
            bad = False
            for target, old, new in patches:
                if old not in texts[target]:
                    bad = True
                    break
                texts[target] = texts[target].replace(old, new, 1)
            if bad:
                results.append((name, "MUTATION-NOT-APPLIED", "snippet not found"))
                restore()
                continue
            WEB.write_text(texts[WEB], encoding="utf-8")
            ART.write_text(texts[ART], encoding="utf-8")

            code, out = run_guard()
            caught = code != 0
            detail = ""
            if caught:
                fails = [l for l in out.splitlines() if l.startswith("FAIL")]
                detail = fails[0][:86] if fails else f"exit {code}"
            else:
                detail = "GUARD PASSED ON A BROKEN TREE"
            results.append((name, "CAUGHT" if caught else "NOT CAUGHT", detail))
            restore()

        # control: clean tree must pass
        restore()
        code, out = run_guard()
        results.append(("CONTROL clean tree passes", "CAUGHT" if code != 0 else "PASS",
                        f"exit {code}"))
    finally:
        restore()

    width = max(len(n) for n, _, _ in results)
    bad = 0
    print()
    for name, verdict, detail in results:
        print(f"  {name.ljust(width)}  {verdict.ljust(10)}  {detail}")
        if verdict in ("NOT CAUGHT", "MUTATION-NOT-APPLIED"):
            bad += 1
        if name.startswith("CONTROL") and verdict != "PASS":
            bad += 1
    print(f"\n=== {len(results) - 1 - bad}/{len(results) - 1} mutations caught"
          f"{'' if bad == 0 else f', {bad} PROBLEM(S)'} ===")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())