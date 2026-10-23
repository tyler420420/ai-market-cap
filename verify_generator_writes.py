#!/usr/bin/env python3
"""Prove the generator actually still writes the HTML artifact.

WHY THIS EXISTS
---------------
2026-10-22. Adding two helper functions to ai_earnings_scanner.py placed them
at module level, but the edit consumed the 4-space comment line that opened
generate_html_report's body. That ended the function early and re-parented the
entire rest of the report - banner, trending cards, table, and the final
`with open(output_path, 'w')` - into the new helper.

The helper ended in `return out`, so the write became UNREACHABLE.

The failure was silent and nasty, because nothing crashed:

  * the scan printed "Generating HTML report..." then "Done!"
  * it still wrote scanner_data.json and the CSV, so the run looked healthy
  * ai_earnings_today.html kept its PREVIOUS mtime and previous contents
  * every existing guard passed, because they all read the stale committed
    artifact - verify_output, verify_trending_cards, verify_paywall, all green
  * git status showed the artifact CLEAN, because the stale file matched HEAD

Two full 4-minute scans produced a correct log and a file that was never
written. Only comparing mtime against the run time caught it.

So: the property worth guarding is not "does the artifact look right" - it is
"does the code path that writes it still exist, and is it reachable".

Run:  python verify_generator_writes.py
Exit 0 = the generator can still write.
"""
import ast
import os
import sys
import time
from pathlib import Path

SITE = Path(r"C:\Users\Tyler_AI\ai-market-cap")
SRC = SITE / "ai_earnings_scanner.py"
ART = SITE / "ai_earnings_today.html"

failures = []


def check(name, ok, detail=""):
    print(("PASS" if ok else "FAIL") + f"  {name}" + ("" if ok else f"  -- {detail}"))
    if not ok:
        failures.append(name)


def write_line_numbers(fn):
    """Line numbers of every `with open(..., 'w')` inside a function."""
    out = []
    for node in ast.walk(fn):
        if not isinstance(node, ast.With):
            continue
        for item in node.items:
            call = item.context_expr
            if not (isinstance(call, ast.Call) and getattr(call.func, "id", "") == "open"):
                continue
            mode = None
            if len(call.args) > 1 and isinstance(call.args[1], ast.Constant):
                mode = call.args[1].value
            for kw in call.keywords:
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                    mode = kw.value.value
            if mode and "w" in str(mode):
                out.append(node.lineno)
    return out


def writes_any(fn):
    return bool(write_line_numbers(fn))


def writes_html(fn):
    """True if this function contains a `with open(..., 'w')` at any depth."""
    return writes_any(fn)


def main():
    tree = ast.parse(SRC.read_text(encoding="utf-8"))
    funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef)]

    gens = [n for n in funcs if n.name == "generate_html_report"]
    check("generate_html_report is defined exactly once", len(gens) == 1,
          f"found {len(gens)}")
    if not gens:
        return 1
    gen = gens[0]

    # 1. the writer is inside the report function, not somewhere else
    write_lines = write_line_numbers(gen)
    check("the HTML write lives inside generate_html_report", bool(write_lines),
          "the artifact would never be written")

    # 2. no HELPER may own a write. This is the exact shape of the bug: the
    #    report body was re-parented into a helper that returns early, so a
    #    write existed in the file but not in any path that runs.
    #    generate_csv_report and main legitimately write their own outputs, so
    #    they are excluded by name rather than by trying to tell their targets
    #    apart in the AST.
    legitimate = {"generate_html_report", "generate_csv_report", "main"}
    offenders = [n.name for n in funcs if n.name not in legitimate and writes_any(n)]
    check("no helper function owns a write (report body re-parented?)",
          not offenders,
          f"{offenders} contain a write - a helper swallowed the report body")

    # 3. the write must be reachable: after the function's own top-level returns
    defs = {n.name: n for n in funcs}
    helper_ends = [defs[n].end_lineno for n in ("_direction_row", "_metric_box") if n in defs]
    for name, end in (("_direction_row", helper_ends[0] if len(helper_ends) > 0 else None),
                      ("_metric_box", helper_ends[1] if len(helper_ends) > 1 else None)):
        if end is None:
            continue
        check(f"{name} ends before generate_html_report starts",
              end < gen.lineno,
              f"{name} spans to line {end} but the report starts at {gen.lineno}")

    # 4. a module-level helper must not contain the report's own statements
    for n in funcs:
        if n.name in ("generate_html_report", "_metric_box", "_direction_row"):
            continue
        if n.lineno < gen.lineno and n.end_lineno > gen.lineno:
            check("no function straddles the start of generate_html_report", False,
                  f"{n.name} ({n.lineno}-{n.end_lineno}) overlaps {gen.lineno}")

    # 5. the write must not be unreachable behind an early return.
    #    An AST check cannot prove a function RUNS, but it can prove the write
    #    is not stranded after an unconditional `return`. That is the other
    #    half of today's bug: the write was inside the right function and still
    #    never executed.
    write_line = min(write_lines) if write_lines else None
    early = [x.lineno for x in gen.body
             if isinstance(x, ast.Return) and write_line and x.lineno < write_line]
    check("no early return can strand the write",
          not early,
          f"generate_html_report returns at line(s) {early} before the write at "
          f"{write_line} - the artifact would never be written")

    # 6. artifact freshness. Off while editing the generator, because touching
    #    the source legitimately makes this fail until a re-scan runs.
    #    SKIP_FRESHNESS=1 is for mutation harnesses and mid-edit checks.
    if os.environ.get("SKIP_FRESHNESS") == "1":
        print("SKIP  artifact freshness (SKIP_FRESHNESS=1)")
    else:
        check("the artifact is newer than the generator source",
              ART.stat().st_mtime >= SRC.stat().st_mtime,
              f"artifact {time.strftime('%H:%M:%S', time.localtime(ART.stat().st_mtime))}"
              f" is OLDER than source "
              f"{time.strftime('%H:%M:%S', time.localtime(SRC.stat().st_mtime))}"
              f" - a run happened and never wrote")

    print(f"\n=== {'ALL PASS' if not failures else str(len(failures)) + ' FAILURE(S)'} ===")
    for f in failures:
        print(f"   - {f}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())