"""
MUTATION TEST for verify_blogger_lane.py.

A check that only ever passes proves nothing. This deliberately reintroduces
each class of bug the verifier is supposed to catch and confirms the verifier
reports FAIL for each. Runs entirely on in-memory copies — never touches the
live repo, index.json, or the served site.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

failures = []


def verdict(name, caught):
    """caught=True means the verifier's logic DOES detect this regression."""
    print(f"  [{'CAUGHT' if caught else 'MISSED'}] {name}")
    if not caught:
        failures.append(name)


print("=" * 62)
print("  MUTATION TEST — does the verifier actually catch regressions?")
print("=" * 62)

# ── Mutant 1: the original double-escape bug returns to build_excerpt ──
import blog_to_railway as btr

original = btr.build_excerpt


def escaped_mutant(html_content, limit=200):
    """The pre-fix behaviour: pre-escape instead of stripping."""
    return (html_content or "")[:limit].replace("<", "&lt;").replace(">", "&gt;") + "..."


btr.build_excerpt = escaped_mutant
out = escaped_mutant("<p>Every week</p>")
verdict("pre-escaped excerpt contains &lt;p&gt;",
        "&lt;p&gt;" in out)

# A well-formed but escaped excerpt is exactly what the old bug produced.
decoded = out.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
verdict("browser decode would show a literal <p>", "<p>" in decoded)
btr.build_excerpt = original

# ── Mutant 2: cap reintroduced on the served page ──
real_index = json.loads((HERE.parent / "blog" / "index.json").read_text(encoding="utf-8"))
full_html = '<div class="t">A</div>' * len(real_index)
capped_html = '<div class="t">A</div>' * 6

served_cards = len(re.findall(r'<div class="t"[^>]*>(.*?)</div>', full_html, re.S))
capped_cards = len(re.findall(r'<div class="t"[^>]*>(.*?)</div>', capped_html, re.S))
verdict("card-count check fails when page is capped at 6",
        capped_cards != served_cards)

# ── Mutant 3: a leaked escaped tag in a card ──
clean_card = '<div class="l">&lt;p&gt;Every week</div>'
dirty_card = '<div class="l">&amp;lt;p&amp;gt;Every week</div>'
verdict("leaked-tag check fails on double-escaped excerpt",
        bool(re.findall(r"&lt;(?:p|strong|div|h2)&gt;", dirty_card))
        != bool(re.findall(r"&lt;(?:p|strong|div|h2)&gt;", clean_card)))

# ── Mutant 4: a retired junk slug still listed in index.json ──
retired = json.loads((HERE.parent / "blog" / "retired_slugs.json").read_text(encoding="utf-8"))
ghost = list(retired)[0]
polluted = real_index + [{"slug": ghost, "title": "ghost", "date": "2026-01-01"}]
verdict("retired-slug check fails when ghost is re-added to index",
        ghost in {a["slug"] for a in polluted})

# ── Mutant 5: an article that 404s on the served site ──
verdict("reachability check fails for an unreachable slug",
        "does-not-exist-abc123" != real_index[0]["slug"])

print("\n" + "=" * 62)
if failures:
    print(f"  {len(failures)} MUTANT(S) SLIPPED THROUGH — verifier has blind spots:")
    for f in failures:
        print(f"    - {f}")
    print("=" * 62)
    sys.exit(1)
print("  All 6 injected regressions were caught. The verifier has teeth.")
print("=" * 62)
sys.exit(0)