#!/usr/bin/env python3
"""Mutation-test verify_generator_writes.py.

WHY
---
On 2026-10-22 the generator silently stopped writing the HTML artifact and
EVERY existing guard stayed green, because they all read the stale committed
file. Two four-minute scans logged "Done!" and wrote nothing.

The new guard exists to catch that. A guard that has never been shown to fail
is a comment, so each mutation below re-creates the real failure shape and
requires a NON-ZERO exit. The final run is the control: clean tree must pass.

  M1  report body re-parented into _direction_row (the actual bug)
  M2  generate_html_report defined twice (the shadowing defect class)
  M3  the write removed from generate_html_report entirely
  M4  _direction_row made to straddle the start of the report

Run:  python prove_generator_writes_bites.py
Exit 0 = every mutation caught AND the clean control passes.
"""
import ast
import os
import subprocess
import sys
from pathlib import Path

SITE = Path(r"C:\Users\Tyler_AI\ai-market-cap")
SRC = SITE / "ai_earnings_scanner.py"
GUARD = SITE / "verify_generator_writes.py"
PY = sys.executable

orig = SRC.read_text(encoding="utf-8")
orig_mtime = SRC.stat().st_mtime
orig_tree = ast.parse(orig)
gen = [n for n in orig_tree.body
       if isinstance(n, ast.FunctionDef) and n.name == "generate_html_report"][0]
gen_start, gen_end = gen.lineno, gen.end_lineno
dr = [n for n in orig_tree.body
      if isinstance(n, ast.FunctionDef) and n.name == "_direction_row"][0]

lines = orig.splitlines(keepends=True)


def m1_reparent_report():
    """Move the entire report body under _direction_row's name.

    Indents every line of generate_html_report by 4 and renames it, exactly
    reproducing what the bad edit did: the report body ends up inside a
    helper that returns early, so the write is unreachable.
    """
    body = lines[gen.lineno - 1:]
    head = lines[:gen.lineno - 1]
    head = [h.replace("def generate_html_report(", "def _direction_row_orphan(")
            for h in head]
    indented = ["    " + l if l.strip() else l for l in body]
    # the orphan keeps the write, and ends with it, so it is structurally
    # "a function that owns a write" - which is exactly what must be flagged
    return "".join(head + indented)


def m2_duplicate_definition():
    """Add a second generate_html_report at the end of the file."""
    clone = "".join(lines[gen_start - 1:gen_end])
    return orig + "\n\n" + clone


def m3_remove_the_write():
    """Turn the write into a READ, so the artifact is never produced.

    Rewriting the mode rather than deleting the `with` line keeps the file
    valid Python - an invalid mutant tests nothing.
    """
    return orig.replace("with open(output_path, 'w', encoding='utf-8') as f:",
                        "with open(output_path, 'r', encoding='utf-8') as f:", 1)


def m4_early_return():
    """Insert an unconditional return at the top of the report function.

    The write stays exactly where it is, inside the right function, and is
    still never executed. No purely structural check could catch this except
    one that looks for a top-level return preceding the write.
    """
    return orig.replace(
        "def generate_html_report(stocks: list, output_path: str):\n",
        "def generate_html_report(stocks: list, output_path: str):\n    return ''\n",
        1)


MUTATIONS = [
    ("M1 report body re-parented into a helper (the real bug)", m1_reparent_report),
    ("M2 generate_html_report defined twice", m2_duplicate_definition),
    ("M3 the HTML write turned into a read", m3_remove_the_write),
    ("M4 unconditional return strands the write", m4_early_return),
]


def restore():
    """Put the file back exactly as it was - content AND mtime.

    Restoring only the content leaves a newer mtime than the generated
    artifact, which then makes verify_generator_writes.py report "a run
    happened and never wrote". The harness must not leave the tree in a state
    that trips an unrelated guard.
    """
    SRC.write_text(orig, encoding="utf-8")
    os.utime(SRC, (orig_mtime, orig_mtime))


def run_guard():
    # SKIP_FRESHNESS: every mutation rewrites the source file, which updates
    # its mtime and would make the freshness check fire for the wrong reason -
    # masking which check actually caught the defect.
    env = dict(os.environ, SKIP_FRESHNESS="1")
    p = subprocess.run([PY, str(GUARD)], capture_output=True, text=True,
                       cwd=str(SITE), timeout=300, env=env)
    return p.returncode, p.stdout + p.stderr


def main():
    results = []
    try:
        for name, fn in MUTATIONS:
            try:
                mutated = fn()
                ast.parse(mutated)          # must at least be valid Python
            except SyntaxError as e:
                results.append((name, "MUTATION-INVALID", f"produced a syntax error: {e}"))
                continue
            SRC.write_text(mutated, encoding="utf-8")
            code, out = run_guard()
            if code != 0:
                fails = [l for l in out.splitlines() if l.startswith("FAIL")]
                detail = fails[0][:80] if fails else f"exit {code}"
                results.append((name, "CAUGHT", detail))
            else:
                results.append((name, "NOT CAUGHT", "GUARD PASSED ON A BROKEN TREE"))
            restore()

        restore()
        code, _ = run_guard()
        results.append(("CONTROL clean tree passes",
                        "PASS" if code == 0 else "FAILED", f"exit {code}"))
    finally:
        restore()

    width = max(len(n) for n, _, _ in results)
    bad = 0
    print()
    for name, verdict, detail in results:
        print(f"  {name.ljust(width)}  {verdict.ljust(12)}  {detail}")
        if verdict in ("NOT CAUGHT", "MUTATION-INVALID") or \
           (name.startswith("CONTROL") and verdict != "PASS"):
            bad += 1
    print(f"\n=== {len(MUTATIONS) - bad}/{len(MUTATIONS)} mutations caught"
          f"{'' if bad == 0 else f', {bad} PROBLEM(S)'} ===")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

