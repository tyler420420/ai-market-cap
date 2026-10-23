"""
TASK 2: fabrication audit.

Extracts every numeric claim from recent articles, classifies it by whether it
is STOCK-SPECIFIC (must be traceable to scanner output / wins page / filing) or
GENERIC TRADING GUIDANCE (position-sizing rules, IV-rank thresholds — standard
practice, not a statistic about a company), and flags any stock-specific figure
that cannot be traced.

Stock-specific = a claim about a named company's price, earnings date, score,
or realised move. Those are the ones that become a complaint if wrong.
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(r"C:\Users\Tyler_AI\ai-market-cap")
sys.path.insert(0, str(REPO / "content_pipeline"))
import quality_gate as qg  # noqa: E402

idx = json.loads((REPO / "blog" / "index.json").read_text(encoding="utf-8"))

# Recent = written by the agent (2026-10-20 onward).
recent = [a for a in idx if a["date"] >= "2026-10-20"]
print(f"Auditing {len(recent)} recent articles (published >= 2026-10-20)\n")

# Claims that name a company/ticker next to a number are stock-specific.
TICKER_CTX = re.compile(
    r"\b(NVDA|AMD|TSLA|META|NBIS|IBM|LRCX|TSM|AVGO|MU|SMCI|CRDO|VRT|DELL|"
    r"INTC|ARM|INOD|SNOW|OKTA|BILI|PANW|NOW|ANET|AMZN|GOOG|GOOGL|MSFT|"
    r"GRAB|TEAM|HOOD|MA|AMAT|TWLO|SHOP|NET|FROG|CDNS|FSLR|SPCX|IREN|"
    r"ORCL|CRM|IBM|QCOM|PLTR|AI)\b"
)

# Industry-wide historical claims: true in general but not attributable to a
# single filing by me. These need a citation or removal.
INDUSTRY_CLAIMS = [
    (r"historically[^.]{0,60}\b\d+%", "historical industry stat"),
    (r"memory (companies|corporations)[^.]{0,80}\d", "historical margin claim"),
    (r"single-digit operating margin", "historical margin claim"),
    (r"thin[^.]{0,40}\bsingle-digit", "historical margin claim"),
]

NUM_PATTERNS = [
    (r"\$\d+(?:\.\d+)?", "dollar figure"),
    (r"\b\d+(?:\.\d+)?%", "percentage"),
    (r"\bIV rank[^.]{0,30}?\b\d+", "IV rank threshold"),
    (r"\b\d+-\d+ (?:to|and) \d+", "range"),
    (r"\b\d+/?\d+-day", "day-count target"),
    (r"\b3/7/14", "target horizon"),
    (r"\b\d+(?:\.\d+)?-day", "day-count"),
]

stock_specific = []
generic = []
industry = []

for a in recent:
    slug = a["slug"]
    html_file = REPO / "blog" / f"{slug}.html"
    if not html_file.exists():
        continue
    html = html_file.read_text(encoding="utf-8")
    # The deployed template writes UNQUOTED attributes: <div class=article-body>.
    # A quoted-only pattern matches nothing and silently audits an empty string,
    # which reported "0 fabrications" while checking nothing at all.
    m = re.search(r'<div class="?article-body"?>(.*?)</div>', html, re.S)
    if not m:
        print(f"  !! could not locate article body in {slug} - SKIPPED, not counted clean")
        continue
    body = m.group(1)
    if len(re.sub(r"<[^>]+>", "", body).split()) < 200:
        print(f"  !! article body too short in {slug} - SKIPPED, not counted clean")
        continue
    text = qg._strip_html(body)
    text = re.sub(r"\s+", " ", text)

    for pat, kind in NUM_PATTERNS:
        for mm in re.finditer(pat, text, re.I):
            s = max(0, mm.start() - 110)
            e = min(len(text), mm.end() + 110)
            ctx = text[s:e].strip()
            rec = {"slug": slug, "kind": kind, "figure": mm.group(0), "ctx": ctx}
            if TICKER_CTX.search(ctx):
                stock_specific.append(rec)
            else:
                generic.append(rec)

    for pat, label in INDUSTRY_CLAIMS:
        for mm in re.finditer(pat, text, re.I):
            s = max(0, mm.start() - 110)
            e = min(len(text), mm.end() + 110)
            industry.append({"slug": slug, "kind": label,
                             "figure": mm.group(0)[:70], "ctx": text[s:e].strip()})

print("=" * 74)
print(f"STOCK-SPECIFIC figures near a named ticker : {len(stock_specific)}")
print("=" * 74)
for r in stock_specific:
    print(f"\n  {r['slug'][:44]}  [{r['kind']}]  {r['figure']}")
    print(f"    ...{r['ctx']}...")

print("\n" + "=" * 74)
print(f"INDUSTRY / HISTORICAL claims needing a citation : {len(industry)}")
print("=" * 74)
for r in industry:
    print(f"\n  {r['slug'][:44]}  [{r['kind']}]")
    print(f"    {r['figure']}")
    print(f"    ...{r['ctx'][:180]}...")

print("\n" + "=" * 74)
print(f"GENERIC trading guidance (position sizing / thresholds): {len(generic)}")
print("  sample:")
for r in generic[:8]:
    print(f"    {r['figure']:<14} ...{r['ctx'][:96]}...")
print(f"\n  (remaining {len(generic) - 8} omitted)")