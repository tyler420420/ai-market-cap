"""Enforce the fabrication standard on rewritten payloads, mechanically.

Every numeric token in a payload's content must either:
  - appear verbatim in VERIFIED_FACTS.md, or
  - be a structural/ordinal value that is clearly not a factual claim
    (years, small ordinals, section numbers).

Anything left over is reported as UNSOURCED and fails the audit. This exists
because "I checked every number" is a claim, not evidence.

Usage:
    python audit_payloads.py
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FACTS = (HERE / "VERIFIED_FACTS.md").read_text(encoding="utf-8")
# Optional argv lets the mutation test run against a scratch copy without
# touching the real payloads directory.
PAYLOADS = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "rewrite_payloads"

TARGET = 1200
META_LO, META_HI = 70, 160

# Normalise the fact pack once: strip $ , % and spaces so "1,200" and "1200" match.
facts_norm = FACTS.replace(",", "").replace("$", "").replace("%", "")

BANNED = [
    "continues to be one of the most discussed topics",
    "this guide covers everything you need to know",
    "represents a meaningful opportunity",
    "let compound results work in your favor",
    "the landscape has shifted considerably",
    "complete guide",
]

# Plain integers/decimals with optional thousands separators and a trailing %.
NUM = re.compile(r"(?<![\w.])(\$?\d[\d,]*(?:\.\d+)?)\s*(%?|percent|billion|million|trillion)?")

# Values that are never factual claims about a company/market here.
STRUCTURAL = {
    "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12",
    "2026", "2027", "2025", "100",
}


def strip_html(h):
    t = re.sub(r"<[^>]+>", " ", h)
    return re.sub(r"&[a-z]+;", " ", t)


def audit(slug):
    p = PAYLOADS / f"{slug}.json"
    if not p.exists():
        return {"slug": slug, "error": "payload file missing"}

    # utf-8-sig: PowerShell 5.1 -Encoding UTF8 writes a BOM, which json.loads
    # rejects. Tolerate both rather than crash on a readable file.
    art = json.loads(p.read_text(encoding="utf-8-sig"))
    content = art.get("content", "")
    meta = art.get("meta_description", "")
    title = art.get("title", "")

    text = strip_html(content)
    words = len([w for w in re.findall(r"[A-Za-z0-9$%.'-]+", text)
                 if any(c.isalnum() for c in w)])

    unsourced = []
    for m in NUM.finditer(text):
        raw, unit = m.group(1), m.group(2)
        val = raw.replace("$", "").replace(",", "")
        if val in STRUCTURAL:
            continue
        # try the value and its common written variants against the fact pack
        cands = {val, val.rstrip("0").rstrip(".") if "." in val else val}
        if unit in ("billion", "million", "trillion"):
            cands.add(val + unit[0])
        if not any(c and c in facts_norm for c in cands):
            ctx = text[max(0, m.start() - 60):m.end() + 60].strip()
            unsourced.append((m.group(0).strip(), ctx))

    h1 = len(re.findall(r"<h1", content, re.I))
    h2 = len(re.findall(r"<h2", content, re.I))
    banned = [b for b in BANNED if b.lower() in (title + " " + content).lower()]

    return {
        "slug": slug,
        "words": words,
        "meta_len": len(meta),
        "h1": h1,
        "h2": h2,
        "title": title,
        "unsourced": unsourced,
        "banned": banned,
        "ok": (words >= TARGET and META_LO <= len(meta) <= META_HI
               and h1 == 0 and h2 >= 3 and not banned
               and len(unsourced) == 0),
    }


def main():
    if not PAYLOADS.exists():
        print("rewrite_payloads/ does not exist yet")
        return 1

    files = sorted(PAYLOADS.glob("*.json"))
    if not files:
        print("no payloads to audit")
        return 1

    print(f"{'slug':<52}{'words':>6}{'meta':>6}{'h2':>4}{'unsourced':>11}  ok")
    print("-" * 92)
    fails = 0
    for f in files:
        r = audit(f.stem)
        if "error" in r:
            print(f"{r['slug'][:52]:<52}  ERROR {r['error']}")
            fails += 1
            continue
        flag = "PASS" if r["ok"] else "FAIL"
        if not r["ok"]:
            fails += 1
        print(f"{r['slug'][:52]:<52}{r['words']:>6}{r['meta_len']:>6}"
              f"{r['h2']:>4}{len(r['unsourced']):>11}  {flag}")
        for val, ctx in r["unsourced"][:6]:
            print(f"      UNSOURCED {val!r} :: ...{ctx[:90]}...")
        if r["h1"]:
            print(f"      H1 PRESENT ({r['h1']}) - articles must not open with H1")
        if r["banned"]:
            print(f"      BANNED PHRASE: {r['banned']}")

    print("-" * 92)
    print(f"{len(files)} payloads, {fails} failing")
    (HERE / "audit_payloads.json").write_text(
        json.dumps([audit(f.stem) for f in files], indent=1), encoding="utf-8")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())