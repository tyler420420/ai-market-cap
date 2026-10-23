"""The "JUST HIT TARGET" nudge must never appear without a real hit.

This banner feeds a sales pitch, so its failure mode is not an ugly page -
it is a page that tells a stranger to pay $5 based on a hit that never
happened. The rules, in order of how badly they would hurt:

  1. No hits          -> renders NOTHING. No placeholder, no "coming soon",
                         no urgency standing in for missing evidence.
  2. Stale file       -> renders NOTHING. If evaluate_targets.py has not run
                         recently the page cannot claim anything is current.
  3. Missing file     -> renders NOTHING, never raises. A pricing page that
                         500s because an optional file is absent is worse
                         than one without a banner.
  4. Hit older than   -> not shown as fresh. The nudge is a nudge, not an
     fresh_days          archive; a 3-month-old hit is not "just".
  5. Every number is copied from the file, never recomputed or rounded up.

The control runs a REAL hit and requires the banner to appear, because a
guard that only ever sees "renders nothing" would pass just as well if the
feature were deleted.
"""
import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path

SITE = Path(r"C:\Users\Tyler_AI\ai-market-cap")
WEB = Path(os.environ.get("WEB_SRC") or (SITE / "scanner_web.py"))

fails = []
ran = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (("  -> " + detail) if detail and not ok else ""))
    ran.append(name)
    if not ok:
        fails.append(name)


def load_web(web_path):
    spec = importlib.util.spec_from_file_location("web_probe", web_path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        return mod
    except Exception:
        # scanner_web.py imports optional deps that may be absent. Extract
        # just the nudge function and exec it with what it needs.
        src = web_path.read_text(encoding="utf-8")
        i = src.index("def _live_hit_nudge(")
        end = src.index("TARGET_HITS_FILE = Path(__file__).parent", i)
        ns = {"json": json, "Path": Path, "print": lambda *a, **k: None}
        exec(compile(src[end:src.index("def _gain_num", end)] + src[i:end], "<nudge>", "exec"), ns)
        return type("M", (), ns)


def _nudge_source():
    """Exact source of _live_hit_nudge via ast.

    Splitting on text is wrong here: the docstring contains blank lines, and
    the function body contains blank lines between blocks, so a delimiter
    lands mid-function. ast does not have that problem.
    """
    import ast as _ast
    src = WEB.read_text(encoding="utf-8")
    tree = _ast.parse(src)
    for node in _ast.walk(tree):
        if isinstance(node, _ast.FunctionDef) and node.name == "_live_hit_nudge":
            return _ast.get_source_segment(src, node)
    raise AssertionError("_live_hit_nudge not found in %s" % WEB)


NUDGE_SRC = _nudge_source()


def nudge_with(payload):
    """Call the real nudge against a given target_hits.json content.

    A regression that makes the nudge RAISE must be reported as a failed
    check, not as a crashed guard. A guard that dies on the bug it exists to
    catch stops the pipeline instead of naming the defect, and it also
    reports the next mutation as "caught" when nothing was actually verified.
    So an exception becomes a non-empty sentinel: every "renders nothing"
    check below already asserts `r == ""`, so a raised exception fails them
    honestly.
    """
    tmp = None
    if payload is not None:
        tmp = Path(tempfile.gettempdir()) / "target_hits_probe.json"
        tmp.write_text(payload if isinstance(payload, str) else json.dumps(payload),
                       encoding="utf-8")
    target = tmp if tmp else Path(r"C:\definitely\not\here\target_hits.json")
    ns = {"json": json, "Path": Path, "print": lambda *a, **k: None}
    try:
        exec(compile(NUDGE_SRC, "<nudge>", "exec"), ns)
        ns["TARGET_HITS_FILE"] = target
        return ns["_live_hit_nudge"]()
    except Exception as e:
        return "\x00RAISED %s: %s" % (type(e).__name__, e)
    finally:
        if tmp and tmp.exists():
            tmp.unlink()


FRESH_HIT = {
    "generated": "2026-10-22T09:00:00",
    "fresh_days": 14,
    "tracked_total": 12, "tracked_in_window": 8, "checked": 8, "unchecked": 0,
    "hit_count": 1,
    "hits": [{"date": "2026-10-12", "ticker": "PANW", "company": "Palo Alto Networks",
              "entry": 354.92, "target": 365.51, "current": 372.10,
              "vs_target_pct": 1.8, "days_to_hit": 10}],
}

STALE_HIT = dict(FRESH_HIT, hits=[dict(FRESH_HIT["hits"][0], days_to_hit=90)])

# --- the honest cases: must render nothing -------------------------------
r = nudge_with(None)
check("no target_hits.json -> renders nothing", r == "", "returned %d chars" % len(r))

r = nudge_with({"fresh_days": 14, "hit_count": 0, "hits": []})
check("zero hits -> renders nothing", r == "", "returned %d chars" % len(r))

r = nudge_with({"fresh_days": 14, "hits": [], "hit_count": 3})
check("hits list empty but hit_count>0 -> renders nothing",
      r == "", "trusts the count instead of the actual hits")

r = nudge_with(STALE_HIT)
check("a hit older than fresh_days -> renders nothing",
      r == "", "a 90-day-old hit was dressed up as 'just'")

r = nudge_with("{ this is not json")
check("corrupt target_hits.json -> renders nothing, no exception",
      r == "", "returned %r" % r[:60])

r = nudge_with({"fresh_days": 14, "hits": ["not-a-dict"]})
check("malformed hit entries -> renders nothing", r == "", "returned %d chars" % len(r))

# --- the control: a real hit MUST render ---------------------------------
r = nudge_with(FRESH_HIT)
check("a real, fresh hit -> the banner appears",
      "JUST HIT TARGET" in r, "the feature is missing, not just silent")
check("the banner names the actual ticker", "PANW" in r)
check("the banner quotes the actual target", "365.51" in r)
check("the banner quotes the actual live price", "372.10" in r)
check("the banner does not invent a number absent from the file",
      "999" not in r and "9999" not in r)

src = WEB.read_text(encoding="utf-8")
check("the pricing page injects the nudge", "_live_hit_nudge()" in src)
check("the nudge is wired into /pricing, not left as dead code",
      src.count("_live_hit_nudge()") >= 2,
      "defined but never called")

runner = SITE / "daily_scan.ps1"
check("daily_scan.ps1 runs the evaluator", runner.exists() and
      "evaluate_targets.py" in runner.read_text(encoding="utf-8", errors="ignore"),
      "nothing would ever produce target_hits.json")

print()
if fails:
    print("RESULT: %d FAILED -> %s" % (len(fails), ", ".join(fails)))
    sys.exit(1)
print("RESULT: ALL PASS (%d checks)" % len(ran))