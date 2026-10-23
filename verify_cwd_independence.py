#!/usr/bin/env python3
"""Every guard must answer the same from any working directory.

WHY THIS EXISTS
On 2026-10-23 EMO ran a guard from the session workspace instead of the repo
root and got a failure on a healthy system. The guards opened repo files by
relative path, so they only ever worked when something else happened to cd
first. run_all_guards.py made it worse by passing cwd=SITE to every child,
which rescued each broken guard inside the suite: green in the runner, red
everywhere else. A check that reports red for a healthy tree is worse than no
check, because it teaches people that red means nothing.

WHAT IT ASSERTS
1. No guard opens a repo file by a path that depends on the process CWD.
   A hardcoded absolute path is acceptable for this purpose - it is still
   CWD-independent. Only a bare filename is the defect.
2. No runner passes cwd= to a spawned guard, because that is the mask that
   hid defect 1 in the first place.

It reads source rather than running anything, so it is safe to run from
anywhere and cannot be fooled by the directory it was launched from.
"""
import ast
import glob
import io
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

PATTERNS = ("verify_*.py", "prove_*.py", "audit_*.py", "run_all_guards.py")
REPO_FILE_EXT = (".py", ".html", ".json", ".txt", ".csv", ".env", ".md", ".log", ".js")

problems = []
checked = 0

targets = []
for pat in PATTERNS:
    targets.extend(glob.glob(str(HERE / pat)))
targets = sorted(set(targets))

for path in targets:
    name = os.path.basename(path)
    # utf-8-sig: several files in this repo carry a BOM and would otherwise
    # fail to parse here, which would silently exempt them from the check.
    try:
        src = io.open(path, encoding="utf-8-sig").read()
    except Exception as e:
        problems.append("%s: could not read (%s)" % (name, e))
        continue
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        problems.append("%s: does not parse (%s)" % (name, e))
        continue

    checked += 1
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        fname = getattr(fn, "id", None) or getattr(fn, "attr", None)

        if fname in ("open", "load_json", "read_text", "read_bytes"):
            args = list(node.args) + [k.value for k in node.keywords]
            for a in args:
                if isinstance(a, ast.Constant) and isinstance(a.value, str):
                    v = a.value
                    if not v.lower().endswith(REPO_FILE_EXT):
                        continue
                    # A bare filename is the defect. ./x, ../x, /x, \x and
                    # C:\x are all CWD-independent.
                    if not any(v.startswith(p) for p in (".", "/", "\\")) and ":" not in v[:3]:
                        problems.append(
                            "%s:%d  opens %r by a CWD-relative path" % (name, node.lineno, v))

        # A guard that spawns another guard by bare filename has the same defect.
        if fname in ("run", "call", "check_call", "Popen") and node.args:
            first = node.args[0]
            if isinstance(first, (ast.List, ast.Tuple)):
                for e in first.elts:
                    if isinstance(e, ast.Constant) and isinstance(e.value, str) \
                            and e.value.endswith(".py") \
                            and not any(e.value.startswith(p) for p in (".", "/", "\\")) \
                            and ":" not in e.value[:3]:
                        problems.append(
                            "%s:%d  spawns %r by a CWD-relative path" % (name, node.lineno, e.value))

# The mask itself. Scoped to run_all_guards.py ON PURPOSE: a runner that sets
# cwd= for every child makes all of them look green inside the suite and red
# outside it, which is how verify_sentiment stayed broken for so long.
#
# Deliberately NOT applied to the prove_*_bites.py harnesses. Those set cwd= to
# a temp directory on purpose - they stage a mutated copy of a guard next to a
# mutated artifact and run the pair. That is isolation, not masking, and a guard
# anchored to __file__ still reads the copy sitting beside it. Flagging those
# would be noise, and noise is what makes people stop reading the output.
RUNNER = HERE / "run_all_guards.py"
if RUNNER.exists():
    rsrc = io.open(RUNNER, encoding="utf-8-sig").read()
    for node in ast.walk(ast.parse(rsrc)):
        if isinstance(node, ast.Call) and (getattr(node.func, "id", None)
                                           or getattr(node.func, "attr", None)) == "run":
            for kw in node.keywords:
                if kw.arg == "cwd":
                    problems.append(
                        "run_all_guards.py:%d  passes cwd= to a spawned guard - that masks "
                        "CWD dependence instead of testing it" % node.lineno)

print("checked %d guard script(s) under %s" % (checked, HERE))
if problems:
    print("\nFAIL - %d CWD-dependence defect(s):" % len(problems))
    for p in problems:
        print("  " + p)
    print("\nA guard must resolve repo files from Path(__file__).resolve().parent,")
    print("not from the process working directory.")
    sys.exit(1)

print("PASS - no guard resolves a repo file through the process CWD")
sys.exit(0)